import argparse
import asyncio

from app.agent.manus import Manus
from app.logger import logger


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Manus agent with a prompt")
    parser.add_argument(
        "--prompt", type=str, required=False, help="Input prompt for the agent"
    )
    args = parser.parse_args()

    # Create and initialize Manus agent
    agent = await Manus.create()
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

        logger.warning("Processing your request...")
        await agent.run(prompt)
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
