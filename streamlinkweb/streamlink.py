import asyncio
import json
import logging
from shlex import quote
from typing import Optional, Union
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_streamlink(
    streamurl: str, quality: Optional[str] = None, proxy: Optional[bool] = False
) -> Union[int, str]:
    """Runs the streamlink command and returns the listening port.

    Args:
        streamurl (str): FQDN of the stream to be played.
        quality (str): Quality of the stream to be played.

    Returns:
        int: Port that the stream is listening on.
    """
    logger.info("Got streamlink request for url: %s", streamurl)
    if quality:
        logger.info("Got streamlink request for quality: %s", quality)

    cmd = [
        "streamlink",
        "--player-external-http",
        "--ffmpeg-ffmpeg",
        "/usr/bin/ffmpeg",
        "--default-stream",
        "best,1080p60,1080p,720p60,720p",
        "--ipv4",
        quote(streamurl),
    ]
    if quality:
        cmd.append(quote(quality))
    if not proxy:
        cmd.append("--json")

    logger.debug("Running streamlink command: %s", cmd)

    proc = await asyncio.create_subprocess_shell(
        " ".join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if not proxy:
        out, err = await proc.communicate()
        if proc.returncode != 0:
            logger.error("Streamlink process returned: %s", proc.returncode)
            logger.error("Streamlink process stdout: %s", out)
            logger.error("Streamlink process stderr: %s", err)
            raise Exception("Streamlink process returned: %s" % proc.returncode)
        return json.loads(out)["url"]

    async for line in proc.stdout:
        line = line.decode("utf-8").strip()
        if "http" in line and not "URL" in line:
            return urlparse(line.removeprefix("[cli][info]  ")).port
    if proc.returncode is not None:
        logger.error("Streamlink process returned: %s", proc.returncode)
        logger.error("Streamlink process stdout: %s", await proc.stdout.read())
        logger.error("Streamlink process stderr: %s", await proc.stderr.read())
        raise Exception("Streamlink process returned: %s" % proc.returncode)
