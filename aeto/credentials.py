def modoDB(modo='despliegue'):
    if modo == 'local':
        return{
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aeto',
        'USER': 'postgres',
        'PASSWORD': '195929',
        'HOST': 'localhost',
        'PORT': '5432',
    }

    if modo == 'despliegue':
        return{
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'aeto',
        'USER': 'super',
        'PASSWORD': 'iGkG1B#@j',
        'HOST': 'carlossantoyo-2681.postgres.pythonanywhere-services.com',
        'PORT': '1025',
    }