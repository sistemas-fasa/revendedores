from django.core.management.base import BaseCommand
from api.models import Cliente


class Command(BaseCommand):
    help = 'Formatea todos los números de cliente con ceros a la izquierda (formato: 00040)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios reales (solo mostrar lo que se haría)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN: No se harán cambios reales'))
        
        clientes = Cliente.objects.all()
        actualizados = 0
        sin_cambios = 0
        errores = 0
        
        self.stdout.write(self.style.SUCCESS(f'\n🔄 Iniciando formateo de números de cliente...'))
        self.stdout.write(f'📊 Total de clientes: {clientes.count()}\n')
        
        for cliente in clientes:
            numero_original = cliente.numero_cliente
            
            # Si el número es válido y no está formateado
            if numero_original and numero_original.strip().isdigit():
                numero_formateado = numero_original.strip().zfill(5)
                
                if numero_original != numero_formateado:
                    try:
                        if not dry_run:
                            cliente.numero_cliente = numero_formateado
                            cliente.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {numero_original.rjust(5)} → {numero_formateado}  ({cliente.nombre})')
                        )
                        actualizados += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Error con cliente {numero_original}: {e}')
                        )
                        errores += 1
                else:
                    sin_cambios += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Cliente {cliente.id} tiene número inválido: "{numero_original}"')
                )
                errores += 1
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n✨ Formateo completado!\n'))
        self.stdout.write(f'📈 Clientes actualizados:  {actualizados}')
        self.stdout.write(f'📊 Clientes sin cambios:   {sin_cambios}')
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errores encontrados:    {errores}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n💡 Ejecuta sin --dry-run para aplicar los cambios'))
