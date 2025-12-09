from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='subcategories',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name  # <-- This makes Django display the category name


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}, {self.country.name}"

class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}, {self.state.name}"

class Taluka(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='talukas')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}, {self.city.name}"

class Village(models.Model):
    taluka = models.ForeignKey(Taluka, on_delete=models.CASCADE, related_name='villages')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}, {self.taluka.name}"


    def __str__(self):
        return self.name

class VerificationDocument(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name