import argparse
import asyncio

from app.agent.manus import Manus
from app.config import config
from app.logger import logger
from app.request_history import log_request, update_request_status
from app.session_workspace import session_workspace


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Manus agent with a prompt")
    parser.add_argument(
        "--prompt", type=str, required=False, help="Input prompt for the agent"
    )
    args = parser.parse_args()

    request_id = None
    agent = None
    try:
        # Use command line prompt if provided, otherwise ask for input
        try:
            from prompt_toolkit import prompt as get_prompt

            print(
                "Enter your prompt (Press Option+Enter or Alt+Enter to add a new line, Enter to submit):"
            )
            user_prompt = (
                args.prompt if args.prompt else get_prompt(">>> ", multiline=False)
            )
        except ImportError:
            user_prompt = args.prompt if args.prompt else input("Enter your prompt: ")

        prompt = user_prompt
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        # Initialize session workspace BEFORE creating agent
        # This ensures agent's system_prompt gets the correct session directory
        session_workspace.set_base_workspace(config.workspace_root)
        session_path = session_workspace.create_session(prompt)
        logger.info(f"Session workspace created: {session_path}")

        # Create and initialize Manus agent AFTER session is created
        agent = await Manus.create()

        # Log request to both logger and history file
        request_id = log_request(prompt, status="started")

        logger.warning("Processing your request...")
        await agent.run(prompt)

        update_request_status(request_id, "completed")
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        if request_id:
            update_request_status(request_id, "interrupted")
        logger.warning("Operation interrupted.")
    except Exception as e:
        if request_id:
            update_request_status(request_id, "failed", str(e))
        raise
    finally:
        # Ensure agent resources are cleaned up before exiting
        if agent:
            await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
