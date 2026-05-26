#!/usr/bin/env python
"""
Script para actualizar números de cliente existentes al formato con ceros a la izquierda (00040)
Ejecutar con: python manage.py shell < actualizar_numeros_cliente.py
O desde el shell de Django: exec(open('actualizar_numeros_cliente.py').read())
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Cliente

def actualizar_numeros_cliente():
    """Actualiza todos los números de cliente al formato con ceros a la izquierda."""
    clientes = Cliente.objects.all()
    actualizados = 0
    
    print("🔄 Iniciando actualización de números de cliente...")
    print(f"📊 Total de clientes: {clientes.count()}")
    
    for cliente in clientes:
        numero_original = cliente.numero_cliente
        
        # Si el número no está en formato correcto, actualizarlo
        if numero_original and numero_original.strip().isdigit():
            numero_formateado = numero_original.strip().zfill(5)
            
            if numero_original != numero_formateado:
                try:
                    cliente.numero_cliente = numero_formateado
                    cliente.save()
                    print(f"✅ Cliente actualizado: {numero_original} → {numero_formateado}")
                    actualizados += 1
                except Exception as e:
                    print(f"❌ Error actualizando cliente {numero_original}: {e}")
    
    print(f"\n✨ Actualización completada!")
    print(f"📈 Clientes actualizados: {actualizados}")
    print(f"📊 Clientes sin cambios: {clientes.count() - actualizados}")

if __name__ == "__main__":
    actualizar_numeros_cliente()
