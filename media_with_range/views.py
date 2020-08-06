#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import io
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseBadRequest


def serve(request: HttpRequest, path: str) -> HttpResponse:
    """
    Serve a file from MEDIA_ROOT.
    """
    local_file_path = Path(settings.MEDIA_ROOT) / Path(path)
    return serve_file(request, local_file_path)


def serve_file(request: HttpRequest, local_file_path: Path):
    if "Range" in request.headers:
        value = request.headers["Range"]

        if not value.startswith("bytes="):
            return HttpResponseBadRequest()

        try:
            _bytes, _equal, range_str = value.partition("=")
            lower_str, _hyphen, upper_str = range_str.partition("-")
            lower = int(lower_str)
            if upper_str:
                upper = int(upper_str)
            else:
                upper = -1

            if lower < 0:
                raise ValueError
            if upper >= 0 and upper < lower:
                raise ValueError

        except ValueError:
            return HttpResponseBadRequest()

        file_contents = local_file_path.read_bytes()
        total_content_length = len(file_contents)

        if upper < 0:
            upper = total_content_length - 1

        partial_file_contents = file_contents[lower : upper + 1]

        response = FileResponse(
            io.BytesIO(partial_file_contents), content_type="audio/m4a",
        )
        response.status_code = 206
        response["Accept-Ranges"] = "bytes"
        response["Content-Range"] = f"bytes {lower}-{upper}/{total_content_length}"
    else:
        response = FileResponse(local_file_path.open("rb"), content_type="audio/m4a",)

    return response
