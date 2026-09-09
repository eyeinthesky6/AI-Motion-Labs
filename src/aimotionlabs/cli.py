from __future__ import annotations

import json
from pathlib import Path

import typer

from aimotionlabs.asset import package_motion_asset, validate_asset
from aimotionlabs.extractors.mediapipe_pose import MediaPipePoseExtractor
from aimotionlabs.models import RightsMetadata
from aimotionlabs.preview import render_skeleton_preview
from aimotionlabs.quality import analyze_asset

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


@app.command("quality")
def quality_report(
    asset: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Analyze motion coverage and temporal QA signals without modifying the asset."""
    report = analyze_asset(asset)
    if json_output:
        typer.echo(json.dumps(report, indent=2))
        return

    typer.echo(f"asset_id: {report['asset_id']}")
    typer.echo(f"coverage: {report['coverage_ratio']:.1%}")
    typer.echo(f"missing frames: {report['missing_frame_ratio']:.1%}")
    confidence = report["confidence"]
    if confidence["mean"] is not None:
        typer.echo(f"confidence mean/p10: {confidence['mean']:.3f} / {confidence['p10']:.3f}")
    velocity = report["joint_velocity"]
    if velocity and velocity["p95"] is not None:
        typer.echo(f"joint velocity p95/max: {velocity['p95']:.3f} / {velocity['max']:.3f}")
    bone_std = report["normalized_bone_length_std"]
    if bone_std is not None:
        typer.echo(f"normalized bone-length std: {bone_std:.4f}")
    for warning in report["warnings"]:
        typer.echo(f"warning: {warning}")


@app.command("preview")
def preview(
    asset: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    source: Path = typer.Option(..., "--source", "-s", exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o", help="Output preview MP4"),
    skeleton_only: bool = typer.Option(False, "--skeleton-only"),
    scale: float = typer.Option(1.0, min=0.1, max=2.0),
) -> None:
    """Render source video with extracted skeleton overlay for human QA."""
    output = render_skeleton_preview(
        asset,
        source,
        out,
        skeleton_only=skeleton_only,
        scale=scale,
    )
    typer.echo(f"Created preview: {output}")


if __name__ == "__main__":
    app()
