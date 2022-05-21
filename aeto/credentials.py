def modoDB(modo='local'):
    # Base de Pruebas
    if modo == 'local':
        return{
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aeto',
        'USER': 'postgres',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '5432',
    }
        
    #Base de despliege aetoweb (No tocar)
    if modo == 'despliege':
        return{
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aeto',
        'USER': 'super',
        'PASSWORD': 'iGkG1B#@j',
        'HOST': 'carlossantoyo-2681.postgres.pythonanywhere-services.com',
        'PORT': '12681',
    }

    #Base de despliegue local (No tocar)
    if modo == 'despliege_local':
        return{
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aeto',
        'USER': 'super',
        'PASSWORD': 'iGkG1B#@j',
        'HOST': '127.0.0.1',
        'PORT': '1025',
    }