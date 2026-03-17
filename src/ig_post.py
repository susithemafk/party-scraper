import asyncio
import mimetypes
import os
import traceback
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


def _debug(message: str) -> None:
    print(f"[IG Post] {message}")


def _mask_token(token: str) -> str:
    token = (token or "").strip()
    if not token:
        return ""
    if len(token) <= 10:
        return "*" * len(token)
    return f"{token[:6]}...{token[-4:]}"


def _raise_with_http_context(response: requests.Response, operation: str) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = (response.text or "").strip().replace("\n", " ")[:1200]
        raise RuntimeError(
            f"{operation} failed (status={response.status_code}) body={body}"
        ) from exc


def _extract_graph_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return (response.text or "").strip().replace("\n", " ")[:1200]

    err = payload.get("error", {}) if isinstance(payload, dict) else {}
    message = err.get("message") if isinstance(err, dict) else ""
    code = err.get("code") if isinstance(err, dict) else ""
    subcode = err.get("error_subcode") if isinstance(err, dict) else ""

    parts = []
    if message:
        parts.append(str(message))
    if code != "":
        parts.append(f"code={code}")
    if subcode != "":
        parts.append(f"subcode={subcode}")

    if parts:
        return " | ".join(parts)
    return (response.text or "").strip().replace("\n", " ")[:1200]


async def validate_instagram_access() -> None:
    ig_config = load_ig_config()
    check_url = f"{ig_config['graph_api_base_url']}/{ig_config['ig_user_id']}"

    _debug(
        "Preflight check: validating Instagram token/session "
        f"for ig_user_id={ig_config['ig_user_id']}"
    )

    def _do_check() -> dict:
        response = requests.get(
            check_url,
            params={
                "fields": "id,username",
                "access_token": ig_config["access_token"],
            },
            timeout=ig_config["request_timeout_seconds"],
        )
        if response.status_code >= 400:
            details = _extract_graph_error_message(response)
            raise RuntimeError(
                "Instagram token preflight failed "
                f"(status={response.status_code}): {details}"
            )
        return response.json()

    payload = await asyncio.to_thread(_do_check)
    _debug(
        "Preflight check passed: "
        f"id={payload.get('id')}, username={payload.get('username', '<unknown>')}"
    )


def _parse_temp_upload_urls(single_url: str, multiple_urls: str) -> list[str]:
    if multiple_urls:
        return [host.strip() for host in multiple_urls.split(",") if host.strip()]
    if single_url:
        return [single_url.strip()]
    return [
        "https://tmpfiles.org/api/v1/upload",
        "https://0x0.st",
    ]


def load_ig_config() -> dict:
    """Build Instagram posting config.

    Prefers values from the city config (if loaded), falling back to raw
    environment variables for backwards compatibility.
    """
    load_dotenv()

    try:
        from .config import get_config

        cfg = get_config()
        access_token = cfg.instagram.meta_access_token
        ig_user_id = cfg.instagram.meta_user_id
        upload_urls = cfg.instagram.temp_image_host_upload_urls or _parse_temp_upload_urls(
            os.getenv("TEMP_IMAGE_HOST_UPLOAD_URL", ""),
            os.getenv("TEMP_IMAGE_HOST_UPLOAD_URLS", ""),
        )
        image_urls = cfg.instagram.image_urls
        graph_api_base_url = (
            cfg.instagram.graph_api_base_url
            or os.getenv("IG_GRAPH_API_BASE_URL", "").strip()
            or "https://graph.facebook.com/v25.0"
        )

        user_agent = (
            cfg.instagram.temp_image_host_user_agent
            or os.getenv("TEMP_IMAGE_HOST_USER_AGENT", "").strip()
            or "brno-events-ig-uploader/1.0 (local script)"
        )

        timeout = int(cfg.instagram.request_timeout_seconds or 60)
    except Exception:
        access_token = os.getenv("META_ACCESS_TOKEN", "").strip()
        ig_user_id = os.getenv("META_USER_ID", "").strip()
        upload_urls = _parse_temp_upload_urls(
            os.getenv("TEMP_IMAGE_HOST_UPLOAD_URL", ""),
            os.getenv("TEMP_IMAGE_HOST_UPLOAD_URLS", ""),
        )
        image_urls = [
            img.strip() for img in os.getenv("IMAGE_URLS", "").split(",") if img.strip()
        ]
        graph_api_base_url = os.getenv(
            "IG_GRAPH_API_BASE_URL", "https://graph.facebook.com/v25.0"
        ).strip()
        user_agent = os.getenv(
            "TEMP_IMAGE_HOST_USER_AGENT",
            "brno-events-ig-uploader/1.0 (local script)",
        )
        timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

    ret = {
        "access_token": access_token,
        "ig_user_id": ig_user_id,
        "image_urls": image_urls,
        "graph_api_base_url": graph_api_base_url,
        "temp_image_host_upload_urls": upload_urls,
        "temp_image_host_user_agent": user_agent,
        "request_timeout_seconds": max(timeout, 1),
    }

    _debug(
        "Config loaded: "
        f"ig_user_id={ret['ig_user_id']}, "
        f"graph_api_base_url={ret['graph_api_base_url']}, "
        f"image_urls={len(ret['image_urls'])}, "
        f"temp_hosts={ret['temp_image_host_upload_urls']}, "
        f"timeout={ret['request_timeout_seconds']}, "
        f"access_token={_mask_token(ret['access_token'])}"
    )

    return ret

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
    ig_config = load_ig_config()
    _debug(f"Uploading via tmpfiles: {image_path.name} (content_type={content_type})")

    def _do_upload():
        with image_path.open("rb") as image_file:
            files = {
                "file": (image_path.name, image_file, content_type)
            }

            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files=files,
                timeout=ig_config["request_timeout_seconds"],
                headers={
                    "User-Agent": ig_config["temp_image_host_user_agent"]},
            )

        _raise_with_http_context(response, "tmpfiles upload")
        payload = response.json()

        if payload.get("status") != "success" or "data" not in payload:
            raise RuntimeError(
                f"tmpfiles.org returned an unexpected payload: {payload}")

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
    ig_config = load_ig_config()
    _debug(
        f"Uploading via temporary host: {upload_url} "
        f"file={image_path.name} (content_type={content_type})"
    )

    def _do_upload():
        with image_path.open("rb") as image_file:
            files = {
                "file": (image_path.name, image_file, content_type)
            }

            response = requests.post(
                upload_url,
                files=files,
                timeout=ig_config["request_timeout_seconds"],
                headers={
                    "User-Agent": ig_config["temp_image_host_user_agent"]},
            )

        _raise_with_http_context(response, f"temporary host upload ({upload_url})")
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
    _debug(f"Resolving local image: {image_path}")

    if not image_path.is_file():
        raise FileNotFoundError(f"Local image not found: {image_path}")

    content_type = mimetypes.guess_type(image_path.name)[
        0] or "application/octet-stream"

    upload_errors = []

    ig_config = load_ig_config()

    for upload_url in ig_config["temp_image_host_upload_urls"]:
        try:
            _debug(f"Trying temp host: {upload_url}")
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
    ig_config = load_ig_config()
    url = f"{ig_config['graph_api_base_url']}/{ig_config['ig_user_id']}/media"
    _debug(
        "Creating image container: "
        f"url={url}, is_single={bool(caption)}, image_url={image_url}"
    )

    # For single image posts
    if caption:
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": ig_config["access_token"],
        }
    else:
        # For carousel items
        payload = {
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": ig_config["access_token"],
        }

    def _create_container():
        response = requests.post(
            url,
            data=payload,
            timeout=ig_config["request_timeout_seconds"],
        )
        _raise_with_http_context(response, "create image container")
        return response.json()["id"]

    container_id = await asyncio.to_thread(_create_container)
    print("Created image container:", container_id)

    return container_id


# Creates a carousel container with the given child media IDs and caption
async def create_carousel_container(children_ids, caption):
    ig_config = load_ig_config()
    url = f"{ig_config['graph_api_base_url']}/{ig_config['ig_user_id']}/media"
    _debug(
        "Creating carousel container: "
        f"url={url}, children_count={len(children_ids)}"
    )

    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
        "access_token": ig_config["access_token"]
    }

    def _create_container():
        response = requests.post(
            url,
            data=payload,
            timeout=ig_config["request_timeout_seconds"],
        )
        _raise_with_http_context(response, "create carousel container")
        return response.json()["id"]

    carousel_id = await asyncio.to_thread(_create_container)
    print("Created carousel container:", carousel_id)

    return carousel_id


# Publishes the media (image or carousel) to Instagram
async def publish_media(container_id):
    ig_config = load_ig_config()
    url = f"{ig_config['graph_api_base_url']}/{ig_config['ig_user_id']}/media_publish"

    payload = {
        "creation_id": container_id,
        "access_token": ig_config["access_token"]
    }

    _debug(
        "Publishing media: "
        f"url={url}, creation_id={container_id}, access_token={_mask_token(ig_config['access_token'])}"
    )

    def _publish():
        response = requests.post(
            url,
            data=payload,
            timeout=ig_config["request_timeout_seconds"],
        )
        _raise_with_http_context(response, "publish media")
        return response.json()

    response_data = await asyncio.to_thread(_publish)
    print("Post published:", response_data)


# Upload multiple images and create a carousel post with a caption
async def upload_multiple_images(image_sources, caption):
    _debug(f"Starting multi-image upload (count={len(image_sources)})")
    children_ids = []

    for index, image_source in enumerate(image_sources, start=1):
        _debug(f"Processing image {index}/{len(image_sources)}: {image_source}")
        image_url = await resolve_image_source(image_source)
        _debug(f"Resolved image {index} URL: {image_url}")
        cid = await create_image_container(image_url)
        children_ids.append(cid)
        _debug(f"Created child container {index}: {cid}")

    await asyncio.sleep(5)
    _debug("Slept 5s before carousel container creation")

    carousel_id = await create_carousel_container(children_ids, caption)
    _debug(f"Created carousel container: {carousel_id}")

    await asyncio.sleep(5)
    _debug("Slept 5s before publish")

    await publish_media(carousel_id)


async def upload_single_image(image_source, caption):
    _debug(f"Starting single-image upload: {image_source}")
    image_url = await resolve_image_source(image_source)
    _debug(f"Resolved single image URL: {image_url}")
    container_id = await create_image_container(image_url, caption)
    _debug(f"Created single-image container: {container_id}")

    await asyncio.sleep(5)

    await publish_media(container_id)


async def upload_media(image_sources, caption):
    _debug(
        f"upload_media called with {len(image_sources)} image(s), "
        f"caption_len={len(caption or '')}"
    )
    if image_sources:
        _debug(f"Image sources preview: {image_sources[:3]}")

    try:
        await validate_instagram_access()
    except Exception as exc:
        _debug(f"Preflight validation failed, aborting upload: {type(exc).__name__}: {exc}")
        raise RuntimeError(
            "Instagram access is not valid anymore. "
            f"Aborting upload. Details: {exc}"
        ) from exc

    try:
        if len(image_sources) == 1:
            _debug("Branch: single image")
            await upload_single_image(image_sources[0], caption)
        else:
            _debug("Branch: multiple images")
            await upload_multiple_images(image_sources, caption)
    except Exception as exc:
        _debug(f"upload_media failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise


async def main():
    from datetime import datetime

    from .config import get_config

    ig_config = load_ig_config()

    if not ig_config["access_token"] or not ig_config["ig_user_id"]:
        raise RuntimeError(
            "Missing ACCESS_TOKEN or IG_USER_ID in environment variables.")

    image_urls = ig_config["image_urls"]
    if not image_urls:
        raise RuntimeError(
            "No image sources provided in IMAGE_URLS environment variable.")

    try:
        cfg = get_config()
        today = datetime.now()
        formatted_date = f"{today.day}. {today.month}. {today.year}"
        caption = cfg.format_caption(formatted_date)
    except Exception:
        caption = "Carousel post from Python 🚀"

    await upload_multiple_images(image_urls, caption)


if __name__ == "__main__":
    asyncio.run(main())
