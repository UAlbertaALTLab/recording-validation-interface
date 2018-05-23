# Run the app in with the custom script name middleware
export FLASK_APP=recval.with_script_name_middleware:create_app
# Our application will live in the /validation subpath.
export FLASK_SCRIPT_NAME=/validation
