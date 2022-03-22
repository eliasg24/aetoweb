# Django
from django.core.files import File

# Utilities
from dashboards.functions import functions
from dashboards.models import FTP, Llanta, Perfil, Vehiculo, Producto, Ubicacion, Aplicacion, Compania
from ftplib import FTP as fileTP
import csv
import os

def ftp_descarga():
    ftp1 = fileTP("208.109.20.121")
    ftp1.login(user="tyrecheck@aeto.com", passwd="TyreDB!25")
    for file_name in ftp1.nlst():
        if not(FTP.objects.filter(file__icontains=file_name).exists()) and not(file_name == "." or file_name == ".."):
            local_file = open(file_name, "wb")
            ftp1.retrbinary("RETR " + file_name, local_file.write)
            archivo = FTP.objects.create()
            archivo.file = file_name
            archivo.save()
            local_file.close()
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
                print(file_name)
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