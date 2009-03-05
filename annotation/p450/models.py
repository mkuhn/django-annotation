from django.db import models

class Protein(models.Model):
    name        = models.TextField()
    annotation  = models.TextField()
    proteinid   = models.CharField(max_length=100, primary_key=True)
    
    class Admin:
        pass

    def __str__(self):
        return self.name

class Food(models.Model):
    foodid      = models.CharField(max_length=100, primary_key=True)
    name        = models.TextField()
    
    def __str__(self):
        return self.name
    
    class Admin:
        pass

class Candidate(models.Model):
    food     = models.ForeignKey(Food)
    protein  = models.ForeignKey(Protein)
    sources  = models.TextField()
    score    = models.DecimalField(max_digits=5, decimal_places=2)
    annotation = models.CharField(max_length=100)
    from_abstract = models.CharField(max_length=100)
    from_file = models.BooleanField()
    
    class Admin:
        pass

    def __str__(self):
        return "\t".join( (self.food.foodid, self.protein.proteinid, self.food.name, self.protein.name, self.annotation, self.from_abstract, self.protein.annotation) )
    
    
    
