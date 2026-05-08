from django.db import models

class Articles(models.Model):
    title = models.CharField('Название', max_length=50)
    full_text = models.TextField('Основной текст')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
