POST

```bash
curl.exe -X POST "http://localhost:8000/api/usuarios/" 
-H "Content-Type: application/json" 
--data-binary "@../body.json"
```

GET

```bash
curl.exe -X GET "http://localhost:8000/api/usuarios/" `
  -H "Content-Type: application/json" 
```