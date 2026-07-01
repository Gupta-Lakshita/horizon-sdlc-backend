license_doc = merge_request_license({})  # same helper already in main.py
try:
    validate_license(
        license_doc,
        pipeline_name="Release Trust",
        target_env="DEV",  # or from request
        requested_features=["release_trust"],
    )
except LicenseValidationError as exc:
    return JSONResponse(
        status_code=403, content={"error": str(exc), "status": "license_denied"}
    )
