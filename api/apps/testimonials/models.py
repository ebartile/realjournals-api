
from django.db import models
from django.core.exceptions import ValidationError

def validate_rating(value):
    if value < 1 or value > 5:
        raise ValidationError("Rating must be between 1 and 5.")

class Testimonial(models.Model):
    author = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True, editable=False)
    rating = models.IntegerField(validators=[validate_rating])
    content = models.TextField()

    def __str__(self):
        return self.author
