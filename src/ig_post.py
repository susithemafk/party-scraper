import asyncio
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from .config import get_config

config = get_config()

ACCESS_TOKEN = config.instagram.meta_access_token
IG_USER_ID = config.instagram.meta_user_id
_single_temp_host = os.getenv("TEMP_IMAGE_HOST_UPLOAD_URL")
_multiple_temp_hosts = os.getenv("TEMP_IMAGE_HOST_UPLOAD_URLS")

if _multiple_temp_hosts:
    TEMP_IMAGE_HOST_UPLOAD_URLS = [
        host.strip() for host in _multiple_temp_hosts.split(",") if host.strip()
    ]
elif _single_temp_host:
    TEMP_IMAGE_HOST_UPLOAD_URLS = [_single_temp_host]
else:
    TEMP_IMAGE_HOST_UPLOAD_URLS = [
        "https://tmpfiles.org/api/v1/upload",
        "https://0x0.st",
    ]

TEMP_IMAGE_HOST_USER_AGENT = os.getenv(
    "TEMP_IMAGE_HOST_USER_AGENT",
    "brno-events-ig-uploader/1.0 (local script)",
)
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

IMAGE_URLS = [
    "img1.jpg",
    "img2.png",
    "img3.jpg"
]

CAPTION = "Carousel post from Python 🚀"

BASE_URL = "https://graph.facebook.com/v25.0"

# Checks if the img source is an HTTP URL or local image
def is_http_url(value):
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

# Converts a tmpfiles.org page URL to a direct download URL if possible.
def _tmpfiles_page_to_direct_url(tmpfiles_url):
    parsed = urlparse(tmpfiles_url)
    parts = [part for part in parsed.path.split("/") if part]

    if parsed.netloc.endswith("tmpfiles.org") and len(parts) >= 2:
        file_id = parts[0]
        filename = "/".join(parts[1:])
        return f"https://tmpfiles.org/dl/{file_id}/{filename}"

    return tmpfiles_url

# Uploads a local image to tmpfiles.org and returns the direct download URL.
async def _upload_with_tmpfiles(image_path, content_type):
    def _do_upload():
        with image_path.open("rb") as image_file:
            files = {
                "file": (image_path.name, image_file, content_type)
            }

            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files=files,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": TEMP_IMAGE_HOST_USER_AGENT},
            )

        response.raise_for_status()
        payload = response.json()

        if payload.get("status") != "success" or "data" not in payload:
            raise RuntimeError(f"tmpfiles.org returned an unexpected payload: {payload}")

        page_url = payload["data"].get("url", "").strip()
        direct_url = _tmpfiles_page_to_direct_url(page_url)

        if not is_http_url(direct_url):
            raise RuntimeError(
                "tmpfiles.org returned an invalid URL: "
                f"{str(page_url)[:200]}"
            )

        return direct_url

    return await asyncio.to_thread(_do_upload)

# Uploads a local image to a generic temporary file hosting service and returns the hosted URL.
async def _upload_with_generic_file_host(image_path, content_type, upload_url):
    def _do_upload():
        with image_path.open("rb") as image_file:
            files = {
                "file": (image_path.name, image_file, content_type)
            }

            response = requests.post(
                upload_url,
                files=files,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": TEMP_IMAGE_HOST_USER_AGENT},
            )

        response.raise_for_status()
        hosted_url = response.text.strip()

        if not is_http_url(hosted_url):
            raise RuntimeError(
                "Temporary image host returned an unexpected response: "
                f"{hosted_url[:200]}"
            )

        return hosted_url

    return await asyncio.to_thread(_do_upload)


# Uploads a local image to a temporary image hosting service and returns the hosted URL.
async def upload_local_image(local_path):
    image_path = Path(local_path).expanduser().resolve()

    if not image_path.is_file():
        raise FileNotFoundError(f"Local image not found: {image_path}")

    content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"

    upload_errors = []

    for upload_url in TEMP_IMAGE_HOST_UPLOAD_URLS:
        try:
            parsed = urlparse(upload_url)
            if "tmpfiles.org" in parsed.netloc:
                hosted_url = await _upload_with_tmpfiles(image_path, content_type)
            else:
                hosted_url = await _upload_with_generic_file_host(image_path, content_type, upload_url)

            print(
                f"Uploaded local image '{image_path}' via '{upload_url}' to temporary URL: {hosted_url}"
            )
            return hosted_url
        except requests.RequestException as exc:
            response = getattr(exc, "response", None)
            status = response.status_code if response is not None else "N/A"
            body_preview = ""

            if response is not None and response.text:
                body_preview = response.text.strip().replace("\n", " ")[:220]

            upload_errors.append(
                f"{upload_url} failed (status={status}): {body_preview or str(exc)}"
            )
        except Exception as exc:
            upload_errors.append(f"{upload_url} failed: {exc}")

    raise RuntimeError(
        "All temporary image hosts failed. "
        "Set TEMP_IMAGE_HOST_UPLOAD_URLS to working endpoints for your network. "
        f"Details: {' | '.join(upload_errors)}"
    )

# Resolves the image source to a URL. If it's already an HTTP URL, returns it as is.
# If it's a local file path, uploads it to a temporary image hosting service and returns the hosted URL.
async def resolve_image_source(image_source):
    image_source = str(image_source).strip()

    if is_http_url(image_source):
        return image_source

    return await upload_local_image(image_source)


# Creates an image container for the given image URL and returns the container ID
async def create_image_container(image_url, caption=""):
    url = f"{BASE_URL}/{IG_USER_ID}/media"

    # For single image posts
    if caption:
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        }
    else:
        # For carousel items
        payload = {
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": ACCESS_TOKEN,
        }

    def _create_container():
        response = requests.post(url, data=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()["id"]

    container_id = await asyncio.to_thread(_create_container)
    print("Created image container:", container_id)

    return container_id


# Creates a carousel container with the given child media IDs and caption
async def create_carousel_container(children_ids, caption):
    url = f"{BASE_URL}/{IG_USER_ID}/media"

    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }

    def _create_container():
        response = requests.post(url, data=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()["id"]

    carousel_id = await asyncio.to_thread(_create_container)
    print("Created carousel container:", carousel_id)

    return carousel_id


# Publishes the media (image or carousel) to Instagram
async def publish_media(container_id):
    url = f"{BASE_URL}/{IG_USER_ID}/media_publish"

    payload = {
        "creation_id": container_id,
        "access_token": ACCESS_TOKEN
    }

    def _publish():
        response = requests.post(url, data=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()

    response_data = await asyncio.to_thread(_publish)
    print("Post published:", response_data)


# Upload multiple images and create a carousel post with a caption
async def upload_multiple_images(image_sources, caption):
    children_ids = []

    for image_source in image_sources:
        image_url = await resolve_image_source(image_source)
        cid = await create_image_container(image_url)
        children_ids.append(cid)

    await asyncio.sleep(5)

    carousel_id = await create_carousel_container(children_ids, caption)

    await asyncio.sleep(5)

    await publish_media(carousel_id)


async def upload_single_image(image_source, caption):
    image_url = await resolve_image_source(image_source)
    container_id = await create_image_container(image_url, caption)

    await asyncio.sleep(5)

    await publish_media(container_id)

async def upload_media(image_sources, caption):
    if len(image_sources) == 1:
        await upload_single_image(image_sources[0], caption)
    else:
        await upload_multiple_images(image_sources, caption)



async def main():

    if not ACCESS_TOKEN or not IG_USER_ID:
        raise RuntimeError("Missing ACCESS_TOKEN or IG_USER_ID in environment variables.")

    if not IMAGE_URLS:
        raise RuntimeError("No image sources provided in IMAGE_URLS environment variable.")
    
    await upload_multiple_images(IMAGE_URLS, CAPTION)


if __name__ == "__main__":
    asyncio.run(main())