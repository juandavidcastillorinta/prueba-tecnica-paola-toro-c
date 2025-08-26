from odoo import models, fields

class TareasRickMorty(models.Model):
    _name = 'tareas.rickmorty'
    _description = 'Tareas de Gestión'

    titulo = fields.Char(string='Título', required=True)
    descripcion = fields.Text(string='Descripción')
    fecha_vencimiento = fields.Date(string='Fecha Vencimiento')
    estado = fields.Selection([
        ('Pendiente', 'Pendiente'),
        ('En progreso', 'En progreso'),
        ('Completada', 'Completada')
    ], string='Estado', required=True)
    id_personaje = fields.Integer(string='ID Personaje RickMorty')