# Archivo que runea todo la app 
from mi_app import app
if __name__ == '__main__':
    app.env='environment'
    app.run(debug=True)