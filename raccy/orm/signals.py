from raccy.core.signals import Signal


class ModelSignal(Signal):

    def notify(self, row_id, model):
        instance = model.objects.get(pk=row_id)
        self._dispatch(instance)


post_save = ModelSignal()
