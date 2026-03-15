import argparse

from src.utils.utils import build_pipeline, load_config, run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="MRZ extraction and document classification pipeline"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "--image",
        help="Optional image path (overrides config)",
    )

    args = parser.parse_args()

    # ---------- LOAD CONFIG ----------
    cfg = load_config(args.config)

    # ---------- BUILD PIPELINE ----------
    pipeline = build_pipeline(cfg)

    # ---------- RUN SERVICE ----------
    run_pipeline(
        pipeline=pipeline,
        cfg=cfg,
        cli_image=args.image,
    )


if __name__ == "__main__":
    main()
