import os
import uvicorn
import argparse
import dotenv

dotenv.load_dotenv()


def main(service: str):
    reload = int(os.getenv("RELOAD", 0)) == 1
    uvicorn.run(
        app=f"services.{service}:server",
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv(f"{service.upper()}_PORT", 5000)),
        reload=reload,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""run specified service with uvicorn server."""
    )
    parser.add_argument(
        "-s",
        "--service",
        required=True,
        default=None,
        help="service to run (default: None)",
    )
    args = parser.parse_args()
    main(**vars(args))
