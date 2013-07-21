class Identity(object):

    def __init__(self,**kwargs):
        def g(k):
            return lambda s: s.kwargs[k]

        self.kwargs = kwargs
        for k in self.kwargs:
            self.parameters[k] = g(k)

    commands = {
    }

    parameters = {}

    constants={
        'class':'identity'
    }
