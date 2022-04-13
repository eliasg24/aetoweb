# Django
from django.core.files import File
from django.contrib.auth.models import User

# Utilities
from dashboards.functions import functions, functions_create
from dashboards.models import Llanta, Perfil, Vehiculo, Producto, Ubicacion, Aplicacion, Compania, Inspeccion
from datetime import date, datetime, timedelta
from ftplib import FTP as fileTP
import csv
import os

def ftp_descarga():
    hoy = date(2022, 4, 12)
    year = hoy.year
    month = hoy.month
    day = hoy.day
    if month < 10:
        month = f"0{month}"
    if day < 10:
        day = f"0{day}"
    ftp1 = fileTP("208.109.20.121")
    ftp1.login(user="tyrecheck@aeto.com", passwd="TyreDB!25")
    for file_name in ftp1.nlst():
        file_type1 = file_name[0:18]

        if file_type1 == f"Products{year}_{month}_{day}":
            local_file = open(file_name, "wb")
            ftp1.retrbinary("RETR " + file_name, local_file.write)
            local_read_file = open(file_name, "r", encoding="utf-8-sig", newline='')
            reader = csv.reader(local_read_file, delimiter=",")
            for row in reader:
                try:
                    if file_type1 == f"Products{year}_{month}_{day}":
                        company = row[1]
                        if company == "NEW PICK" or company == "Tramo" or company == "SOLAQRO":
                            if company == "NEW PICK":
                                company = Compania.objects.get(compania="New Pick")
                            elif company == "Tramo":
                                company = Compania.objects.get(compania="Tramo")
                            elif company == "SOLAQRO":
                                company = Compania.objects.get(compania="SOLAQRO")
                            try:
                                producto = Producto.objects.get(producto=row[4])
                                marca = row[6]
                                dibujo = row[7]
                                dimension = row[8]
                                profundidad_inicial = int(float(row[10]))
                                vida = row[9]
                                if vida == "New":
                                    vida = "Nueva"
                                elif vida == "Retread":
                                    vida = "Renovada"
                                precio = row[12]
                                if precio == "":
                                    precio = 2000
                                else:
                                    precio = int(float(row[12]))
                                producto.marca=marca
                                producto.dibujo=dibujo
                                producto.dimension=dimension
                                producto.profundidad_inicial=profundidad_inicial
                                producto.vida=vida
                                producto.precio=precio
                                producto.save()
                            except:
                                marca = row[6]
                                dibujo = row[7]
                                dimension = row[8]
                                profundidad_inicial = int(float(row[10]))
                                vida = row[9]
                                if vida == "New":
                                    vida = "Nueva"
                                elif vida == "Retread":
                                    vida = "Renovada"
                                precio = row[12]
                                if precio == "":
                                    precio = 2000
                                else:
                                    precio = int(float(row[12]))

                                Producto.objects.create(producto=row[4],
                                                        marca=marca,
                                                        dibujo=dibujo,
                                                        dimension=dimension,
                                                        profundidad_inicial=profundidad_inicial,
                                                        vida=vida,
                                                        precio=precio
                                                    )

                except:
                    pass
            local_file.close()
            local_read_file.close()
            os.remove(os.path.abspath(file_name))

    for file_name in ftp1.nlst():
        file_type1 = file_name[0:18]

        if file_type1 == f"Vehicles{year}_{month}_{day}":
            local_file = open(file_name, "wb")
            ftp1.retrbinary("RETR " + file_name, local_file.write)
            local_read_file = open(file_name, "r", encoding="utf-8-sig", newline='')
            reader = csv.reader(local_read_file, delimiter=",")
            for row in reader:
                try:
                    if file_type1 == f"Vehicles{year}_{month}_{day}":
                        company = row[3]
                        if company == "NEW PICK SA DE CV" or company == "CSI" or company == "MPV360" or company == "SOLAQRO":
                            if company == "NEW PICK SA DE CV":
                                company = Compania.objects.get(compania="New Pick")
                            elif company == "CSI":
                                company = Compania.objects.get(compania="CSI")
                            elif company == "MPV360":
                                company = Compania.objects.get(compania="TDR")
                            elif company == "SOLAQRO":
                                company = Compania.objects.get(compania="SOLAQRO")
                            try:
                                vehiculo = Vehiculo.objects.get(numero_economico=row[9], compania=company)
                            except:
                                status = row[20]
                                if status != "Inactive":
                                    try:
                                        ubicacion = Ubicacion.objects.get1(nombre=row[5], compania=company)
                                    except:
                                        ubicacion = Ubicacion.objects.create(nombre=row[5], compania=company)
                                    try:
                                        aplicacion = Aplicacion.objects.get(nombre=row[7], compania=company)
                                    except:
                                        aplicacion = Aplicacion.objects.create(nombre=row[7], compania=company)

                                    if km == "":
                                        km = None
                                    else:
                                        km = int(float(row[10]))
                                    functions_create.crear_clase(row[12])
                                    fecha_de_creacion = row[21]
                                    fecha_de_creacion = functions.convertir_fecha3(fecha_de_creacion)
                                    vehiculo = Vehiculo.objects.create(numero_economico=row[9],
                                                                    modelo=row[18],
                                                                    marca=row[16],
                                                                    compania=company,
                                                                    ubicacion=ubicacion,
                                                                    aplicacion=aplicacion,
                                                                    numero_de_llantas = functions.cantidad_llantas(row[14]),
                                                                    clase = row[12].upper(),
                                                                    configuracion = row[14],
                                                                    km=km,
                                                                    fecha_de_creacion=fecha_de_creacion,
                                                                    tirecheck=True
                                                                    )
                except:
                    break
            local_file.close()
            local_read_file.close()
            os.remove(os.path.abspath(file_name))

    """for file_name in ftp1.nlst():
        file_type5 = file_name[0:22]

        if file_type5 == f"RollingStock{year}_{month}_{day}":
            local_file = open(file_name, "wb")
            ftp1.retrbinary("RETR " + file_name, local_file.write)
            local_read_file = open(file_name, "r", encoding="utf-8-sig", newline='')
            reader = csv.reader(local_read_file, delimiter=",")
            for row in reader:
                if file_type5 == f"RollingStock{year}_{month}_{day}":
                    company = row[1]
                    if company == "NEW PICK SA DE CV":
                        company = Compania.objects.get(compania="New Pick")
                        numero_economico = row[9]
                        try:
                            llanta = Llanta.objects.get(numero_economico=numero_economico, compania=company)
                            vehiculo = Vehiculo.objects.get(numero_economico=row[6], compania=company)
                        except:
                            try:
                                usuario = Perfil.objects.get(user=User.objects.get(username="NewPick"))
                                vehiculo = Vehiculo.objects.get(numero_economico=row[6], compania=company)
                                vida = row[15]
                                if vida == "New":
                                    vida = "Nueva"
                                elif vida == "1st Retread":
                                    vida = "1R"
                                elif vida == "2st Retread":
                                    vida = "2R"
                                elif vida == "3st Retread":
                                    vida = "3R"
                                elif vida == "4st Retread":
                                    vida = "4R"
                                elif vida == "Retread":
                                    vida = "1R"

                                posicion = row[7]
                                tipo_de_eje = functions.sacar_eje(int(posicion[0]), vehiculo)
                                eje = int(posicion[0])

                                if tipo_de_eje[0] == "S":
                                    nombre_de_eje = "Dirección"
                                elif tipo_de_eje[0] == "D":
                                    nombre_de_eje = "Tracción"
                                elif tipo_de_eje[0] == "T":
                                    nombre_de_eje = "Arrastre"
                                elif tipo_de_eje[0] == "C":
                                    nombre_de_eje = "Loco"
                                elif tipo_de_eje[0] == "L":
                                    nombre_de_eje = "Retractil"

                                producto = row[10]
                                try:
                                    producto = Producto.objects.get(producto=producto)
                                except:
                                    producto = Producto.objects.create(producto=producto)

                                inventario = "Rodante"
                                km_montado = row[13]
                                if km_montado == "":
                                    km_montado = None
                                else:
                                    km_montado = int(float(row[13]))

                                Llanta.objects.create(numero_economico=numero_economico,
                                                    usuario=usuario,
                                                    compania=company,
                                                    vehiculo=vehiculo,
                                                    ubicacion=vehiculo.ubicacion,
                                                    vida=vida,
                                                    tipo_de_eje=tipo_de_eje,
                                                    eje=eje,
                                                    posicion=posicion,
                                                    nombre_de_eje=nombre_de_eje,
                                                    producto=producto,
                                                    inventario=inventario,
                                                    km_montado=km_montado,
                                                    tirecheck=True
                                                    )
                            except:
                                pass


            local_file.close()
            local_read_file.close()
            os.remove(os.path.abspath(file_name))

    for file_name in ftp1.nlst():
        file_type2 = file_name[0:15]

        if file_type2 == f"Stock{year}_{month}_{day}":
            local_file = open(file_name, "wb")
            ftp1.retrbinary("RETR " + file_name, local_file.write)
            local_read_file = open(file_name, "r", encoding="utf-8-sig", newline='')
            reader = csv.reader(local_read_file, delimiter=",")
            for row in reader:
                try:
                    if file_type2 == f"Stock{year}_{month}_{day}":
                        company = row[1]
                        if company == "NEW PICK SA DE CV":
                            company = Compania.objects.get(compania="New Pick")
                            numero_economico = row[7]
                            try:
                                llanta = Llanta.objects.get(numero_economico=numero_economico, compania=company)
                            except:
                                usuario = Perfil.objects.get(user=User.objects.get(username="NewPick"))
                                vida = row[14]
                                if vida == "New":
                                    vida = "Nueva"
                                elif vida == "1st Retread":
                                    vida = "1R"
                                elif vida == "2st Retread":
                                    vida = "2R"
                                elif vida == "3st Retread":
                                    vida = "3R"
                                elif vida == "4st Retread":
                                    vida = "4R"
                                elif vida == "Retread":
                                    vida = "1R"

                                producto = row[8]
                                try:
                                    producto = Producto.objects.get(producto=producto)
                                except:
                                    producto = Producto.objects.create(producto=producto)

                                inventario = row[5]
                                if inventario == "RollingStock":
                                    inventario = "Rodante"
                                elif inventario == "ForScrapStock":
                                    inventario = "Antes de Desechar"
                                elif inventario == "ForServiceStock":
                                    inventario = "Servicio"
                                else:
                                    inventario = None
                                try:
                                    km_montado = int(row[12])
                                except:
                                    km_montado = None
                                Llanta.objects.create(numero_economico=numero_economico,
                                                    usuario=usuario,
                                                    compania=company,
                                                    vida=vida,
                                                    producto=producto,
                                                    inventario=inventario,
                                                    km_montado=km_montado,
                                                    tirecheck=True
                                                    )
                except:
                    break
            local_file.close()
            local_read_file.close()
            os.remove(os.path.abspath(file_name))"""

    for file_name in ftp1.nlst():
        file_type6 = file_name[0:11]

        if file_type6 == f"Inspections" and file_name != "Inspections_Bulk_01142022.csv" and file_name != "Inspections.csv":
            print(file_name)
            local_file = open(file_name, "wb")
            ftp1.retrbinary("RETR " + file_name, local_file.write)
            local_file.close()

            with open(file_name, 'r', encoding="utf-8-sig", newline='') as local_read_file:

                reader = csv.reader(local_read_file)

                for row in reader:
                    try:
                        if file_type6 == f"Inspections" and file_name != "Inspections_Bulk_01142022.csv" and file_name != "Inspections.csv":
                            company = row[1]
                            if company == "NEW PICK SA DE CV" or company == "CSI" or company == "MPV360" or company == "SOLAQRO":
                                if company == "NEW PICK SA DE CV":
                                    company = Compania.objects.get(compania="New Pick")
                                elif company == "CSI":
                                    company = Compania.objects.get(compania="CSI")
                                elif company == "MPV360":
                                    company = Compania.objects.get(compania="TDR")
                                elif company == "SOLAQRO":
                                    company = Compania.objects.get(compania="SOLAQRO")
                                llanta = row[12]

                                try:
                                    llanta_hecha = Llanta.objects.get(numero_economico=llanta, compania=company)
                                except:
                                    llanta_hecha = None
                                if llanta_hecha:
                                    fecha_hora = row[4]
                                    fecha_hora = functions.convertir_fecha4(fecha_hora)
                                    km = row[6]
                                    if km == "":
                                        km = 2000
                                    else:
                                        km = int(float(row[6]))

                                    profundidades = [float(row[18]), float(row[19]), float(row[20])]
                                    min_profundidad = min(profundidades)
                                    max_profundidad = max(profundidades)

                                    presion = float(row[21])
                                    presion = int(presion * 14.5038)

                                    try:
                                        observacion_1 = row[22]
                                    except:
                                        observacion_1 = None
                                    try:
                                        observacion_2 = row[23]
                                    except:
                                        observacion_2 = None
                                    try:
                                        observacion_3 = row[24]
                                    except:
                                        observacion_3 = None

                                    inspeccion_creada = Inspeccion.objects.create(llanta=llanta_hecha,
                                                            fecha_hora=fecha_hora,
                                                            km=km,
                                                            presion=presion,
                                                            min_profundidad=min_profundidad,
                                                            max_profundidad=max_profundidad,
                                                            observacion_1=observacion_1,
                                                            observacion_2=observacion_2,
                                                            observacion_3=observacion_3
                                    )
                                    if llanta_hecha.ultima_inspeccion:
                                        fecha_ultima_inspeccion = llanta_hecha.ultima_inspeccion.fecha_hora
                                        fecha_inspeccion_actual = inspeccion_creada.fecha_hora
                                        if fecha_ultima_inspeccion.timestamp() > fecha_inspeccion_actual.timestamp():
                                            pass
                                        else:
                                            llanta_hecha.ultima_inspeccion = inspeccion_creada
                                            llanta_hecha.save()
                                    else:
                                        llanta_hecha.ultima_inspeccion = inspeccion_creada
                                        llanta_hecha.save()

                                    try:
                                        vehiculo = Vehiculo.objects.get(numero_economico=llanta_hecha.vehiculo.numero_economico)
                                        vehiculo.ultima_inspeccion = inspeccion_creada
                                        vehiculo.save()
                                    except:
                                        pass
                    except:
                        pass


                local_read_file.close()
                os.remove(os.path.abspath(file_name))

    ftp1.quit()


def ftp1():

    DIR = "D:/Aetoweb/aeto/"
    DIR_PATH = os.listdir(DIR)
    ftp2 = fileTP("208.109.20.121")
    ftp2.login(user="tdr@aeto.com", passwd="486dbintegracion!")
    for FILE_PATH in DIR_PATH:
        file_type1 = FILE_PATH[0:10]
        file_type2 = FILE_PATH[0:7]
        file_type3 = FILE_PATH[0:10]
        file_type4 = FILE_PATH[0:15]
        file_type5 = FILE_PATH[0:14]
        file_type6 = FILE_PATH[0:13]
        file_type7 = FILE_PATH[0:8]
        if file_type1 == "Vehicles20" or file_type2 == "Stock20" or file_type3 == "Services20" or file_type4 == "ScrappedTires20" or file_type5 == "RollingStock20" or file_type6 == "Inspections20" or file_type7 == "Casing20":
            file = open(DIR + FILE_PATH, "r", encoding="utf-8-sig", newline='')
            reader = csv.reader(file, delimiter=",")
            file_write = open("TDR_" + FILE_PATH, "w", encoding="utf-8-sig", newline='')
            writer = csv.writer(file_write, delimiter=",")

            csv_dict_reader = csv.DictReader(file)
            column_names = csv_dict_reader.fieldnames
            writer.writerow(column_names)

            for row in reader:
                try:
                    if file_type1 == "Vehicles20":
                        company = row[3]
                    elif file_type2 == "Stock20":
                        company = row[1]
                    elif file_type3 == "Services20":
                        company = row[1]
                    elif file_type4 == "ScrappedTires20":
                        company = row[0]
                    elif file_type5 == "RollingStock20":
                        company = row[1]
                    elif file_type6 == "Inspections20":
                        company = row[1]
                    elif file_type7 == "Casing20":
                        company = row[8]
                except:
                    break
                if company == "MPV360":
                    writer.writerow(row)

            file.close()
            file_write.close()

            file_read = open("TDR_" + FILE_PATH, "rb")

            ftp2.storbinary('STOR ' + "TDR_" + FILE_PATH, file_read)
            file_read.close()
            os.remove(os.path.abspath("TDR_" + FILE_PATH))

            os.remove(os.path.abspath(FILE_PATH))
    ftp2.quit()

def ftp2(user):

    DIR = "D:/Aetoweb/aeto/"
    ftp1 = fileTP("208.109.20.121")
    ftp1.login(user="tyrecheck@aeto.com", passwd="TyreDB!25")
    for file_name in ftp1.nlst():
        file_type1 = file_name[0:10]
        file_type2 = file_name[0:7]
        file_type3 = file_name[0:10]
        file_type4 = file_name[0:15]
        file_type5 = file_name[0:14]
        file_type6 = file_name[0:13]
        file_type7 = file_name[0:8]
        if file_type1 == "Vehicles20" or file_type2 == "Stock20" or file_type3 == "Services20" or file_type4 == "ScrappedTires20" or file_type5 == "RollingStock20" or file_type6 == "Inspections20" or file_type7 == "Casing20":
            local_file = open(file_name, "wb")
            ftp1.retrbinary("RETR " + file_name, local_file.write)
            file = open(DIR + file_name, "r", encoding="utf-8-sig", newline='')
            reader = csv.reader(file, delimiter=",")
            if file_type1 == "Vehicles20":
                for row in reader:
                    compania = row[3]
                    if compania == "MPV360":
                        company = Compania.objects.get(compania="TDR")
                        ubicacion = Ubicacion.objects.create(nombre=row[5], compania=company)
                        aplicacion = Aplicacion.objects.create(nombre=row[7], compania=company)
                        vehiculo = Vehiculo.objects.create(numero_economico=row[9],
                                                        modelo=row[18],
                                                        marca=row[16],
                                                        compania=company,
                                                        ubicacion=ubicacion,
                                                        aplicacion=aplicacion,
                                                        numero_de_llantas = functions.cantidad_llantas(row[14]),
                                                        clase = row[12],
                                                        configuracion = row[14]
                                                        )
            """if file_type1 == "Stock20":
                for row in reader:
                    compania = row[1]
                    if compania == "MPV360":
                        llanta = Llanta.objects.create()
                        llanta.numero_economico = row[7]
                        llanta.usuario = Perfil.objects.get(user=user)
                        llanta.vehiculo = row[18]
                        vida = row[14]
                        if vida == "New":
                            vida = "Nueva"
                        elif vida == "1st Retread":
                            vida = "1R"
                        elif vida == "2st Retread":
                            vida = "2R"
                        elif vida == "3st Retread":
                            vida = "3R"
                        elif vida == "Retread":
                            vida = "4R"

                        llanta.vida = vida
                        producto = Producto.objects.create(producto=row[8])
                        llanta.producto = producto
                        llanta.modelo = row[18]
                        llanta.marca = row[16]
                        llanta.compania = row[3]
                        llanta.ubicacion = row[5]
                        llanta.aplicacion = row[7]
                        llanta.numero_de_llantas = functions.cantidad_llantas(row[14])
                        llanta.clase = row[12]
                        llanta.configuracion = row[14]
                        llanta.save()"""
            file.close()
            local_file.close()
            os.remove(os.path.abspath(file_name))

    ftp1.quit()



    """if file_type1 == "Vehicles20" or file_type2 == "Stock20" or file_type3 == "Services20" or file_type4 == "ScrappedTires20" or file_type5 == "RollingStock20" or file_type6 == "Inspections20" or file_type7 == "Casing20":
        file = open(DIR + FILE_PATH, "r", encoding="utf-8-sig", newline='')
        reader = csv.reader(file, delimiter=",")
        file_write = open("TDR_" + FILE_PATH, "w", encoding="utf-8-sig", newline='')
        writer = csv.writer(file_write, delimiter=",")

        csv_dict_reader = csv.DictReader(file)
        column_names = csv_dict_reader.fieldnames
        writer.writerow(column_names)


        for row in reader:
            try:
                if file_type1 == "Vehicles20":
                    company = row[3]
                elif file_type2 == "Stock20":
                    company = row[1]
                elif file_type3 == "Services20":
                    company = row[1]
                elif file_type4 == "ScrappedTires20":
                    company = row[0]
                elif file_type5 == "RollingStock20":
                    company = row[1]
                elif file_type6 == "Inspections20":
                    company = row[1]
                elif file_type7 == "Casing20":
                    company = row[8]
            except:
                break
            if company == "MPV360":
                writer.writerow(row)



        file.close()
        file_write.close()

        file_read = open("TDR_" + FILE_PATH, "rb")

        ftp2.storbinary('STOR ' + "TDR_" + FILE_PATH, file_read)
        file_read.close()
        os.remove(os.path.abspath("TDR_" + FILE_PATH))

        os.remove(os.path.abspath(FILE_PATH))
    ftp2.quit()"""