"""
Copyright 2021 Daniel Afriyie

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from raccy.core.signals import Signal


class ModelPostSaveSignal(Signal):

    def notify(self, row_id, model):
        instance = model.objects.get(pk=row_id)
        self._dispatch(instance)


post_save = ModelPostSaveSignal()
