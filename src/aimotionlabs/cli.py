from __future__ import annotations

from pathlib import Path

import typer

from aimotionlabs.asset import package_motion_asset, validate_asset
from aimotionlabs.extractors.mediapipe_pose import MediaPipePoseExtractor
from aimotionlabs.models import RightsMetadata

app = typer.Typer(
    name="motionlab",
    help="Video-to-MotionSpec tools for AI Motion Labs.",
    no_args_is_help=True,
)


@app.command()
def extract(
    video: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o", help="Output .motion directory"),
    model: Path = typer.Option(
        ...,
        "--model",
        help="Path to a MediaPipe Pose Landmarker .task model",
        exists=True,
        dir_okay=False,
        readable=True,
    ),
    attest_rights: bool = typer.Option(
        False,
        "--attest-rights",
        help="Record that the uploader claims the right to process/reuse this source",
    ),
) -> None:
    """Extract a short single-person video into a MotionSpec v0.1 asset."""
    extractor = MediaPipePoseExtractor(model)
    typer.echo(f"Extracting motion from {video} ...")
    extracted = extractor.extract(video)

    rights = RightsMetadata(
        source_attestation="user_claims_rights" if attest_rights else "unknown",
        public_share_allowed=False,
        notes="Public sharing remains off by default in v0.1.",
    )
    manifest = package_motion_asset(
        video_path=video,
        extracted=extracted,
        out_dir=out,
        rights=rights,
    )
    typer.echo(f"Created {manifest.asset_id} at {out}")
    typer.echo(
        f"Frames: {len(extracted.timestamps_ms)} | "
        f"missing pose: {manifest.quality.missing_frame_ratio:.1%}"
    )


@app.command()
def validate(
    asset: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Validate a MotionSpec manifest against its payload files."""
    manifest = validate_asset(asset)
    typer.echo(f"OK: {manifest.asset_id} ({manifest.schema_name} {manifest.schema_version})")
    for warning in manifest.quality.warnings:
        typer.echo(f"warning: {warning}")


@app.command()
def inspect(
    asset: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Print a compact summary of a MotionSpec asset."""
    manifest = validate_asset(asset)
    typer.echo(f"asset_id: {manifest.asset_id}")
    typer.echo(f"source: {manifest.source.original_filename}")
    typer.echo(f"duration_s: {manifest.source.duration_s:.3f}")
    typer.echo(f"extractor: {manifest.extractor.name}")
    typer.echo(f"tracks: {', '.join(track.id for track in manifest.tracks)}")
    typer.echo(f"public_share_allowed: {manifest.rights.public_share_allowed}")


if __name__ == "__main__":
    app()
