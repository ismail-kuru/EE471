"""Turn an image into the JSON file Postman sends to Cog's /predictions endpoint.

Cog only accepts JSON, so the image has to be inside the request as a base64 data URI.
Usage: python3 make_postman_body.py cat.jpg
"""

import base64
import json
import mimetypes
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit("Usage: python3 make_postman_body.py <image file>")

image = Path(sys.argv[1])
mime_type = mimetypes.guess_type(image.name)[0] or "image/jpeg"
encoded = base64.b64encode(image.read_bytes()).decode()

output = image.with_name(f"{image.stem}-request.json")
output.write_text(json.dumps({"input": {"image": f"data:{mime_type};base64,{encoded}"}}))
print(f"Wrote {output}")
