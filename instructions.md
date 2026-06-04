# Create virtual environment and activate it

python -m venv venv
source venv/bin/activate

# run uvicorn server

uvicorn main:app --reload --port 8000

# Open the psql super admin

sudo -u postgres psql

# Now install packages

pip install -r requirements.txt

# Open the wsl folders from the terminal

explorer.exe .

# steps to get the backend infos

go to http://localhost:8000/openapi.json

install the generator from the frontend: <npm install --save-dev openapi-typescript>

add to package.json: <{
"scripts": {
"generate-api": "openapi-typescript lib/api/openapi.json -o lib/api/types.ts"
}
}>

run this from the frontend to generate the types: npm run generate-api
