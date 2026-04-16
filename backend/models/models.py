from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
import datetime
from core.database import Base

class Taller(Base):
    __tablename__ = "talleres"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    activation_key = Column(String, unique=True, index=True) # Llave de activación única
    fecha_vencimiento = Column(DateTime, nullable=True) # Fecha de expiración de suscripción
    whatsapp_api_key = Column(String, nullable=True)
    suscripcion_activa = Column(Boolean, default=True) # KILL SWITCH
    plan = Column(String, default="Basico")
    
    empleados = relationship("Empleado", back_populates="taller")
    registros = relationship("Registro", back_populates="taller")
    finanzas = relationship("Finanzas", back_populates="taller")
    dispositivos = relationship("Dispositivo", back_populates="taller")

class Dispositivo(Base):
    __tablename__ = "dispositivos"
    
    id = Column(Integer, primary_key=True, index=True)
    taller_id = Column(Integer, ForeignKey("talleres.id"))
    hw_id = Column(String, unique=True, index=True) # Serial del disco / Machine GUID
    nombre_pc = Column(String)
    ultima_conexion = Column(DateTime, default=datetime.datetime.utcnow)
    
    taller = relationship("Taller", back_populates="dispositivos")

class Empleado(Base):
    __tablename__ = "empleados"
    
    id = Column(Integer, primary_key=True, index=True)
    taller_id = Column(Integer, ForeignKey("talleres.id"))
    nombre = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    rol = Column(String) # Admin, Mecanico, Recepcion
    
    taller = relationship("Taller", back_populates="empleados")

class Registro(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, index=True)
    taller_id = Column(Integer, ForeignKey("talleres.id"))
    nombre_cliente = Column(String)
    telefono_cliente = Column(String)
    vehiculo = Column(String)
    placas = Column(String)
    servicio = Column(String)
    costo_proyectado = Column(Float, default=0.0)
    estado = Column(String, default="Pendiente") # Lead, Aprobado, Reparando, Listo, Entregado
    fecha_ingreso = Column(DateTime, default=datetime.datetime.utcnow)
    
    taller = relationship("Taller", back_populates="registros")
    finanzas = relationship("Finanzas", back_populates="registro")

class Finanzas(Base):
    __tablename__ = "finanzas"
    
    id = Column(Integer, primary_key=True, index=True)
    taller_id = Column(Integer, ForeignKey("talleres.id"))
    registro_id = Column(Integer, ForeignKey("registros.id"), nullable=True) # Opcional: Puede ser un gasto de luz (sin registro)
    tipo = Column(String) # INGRESO, EGRESO
    concepto = Column(String)
    monto = Column(Float)
    fecha = Column(DateTime, default=datetime.datetime.utcnow)
    
    taller = relationship("Taller", back_populates="finanzas")
    registro = relationship("Registro", back_populates="finanzas")
