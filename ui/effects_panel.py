from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import effects.basic_effects  # noqa: F401  (enregistre les effets de base)
from effects.base_effect import EffectInstance, get_available_effects


class EffectsPanel(QWidget):
    """Panneau listant les effets disponibles, avec leurs paramètres, à appliquer au clip sélectionné."""

    effect_applied = Signal(object, object)  # (clip, EffectInstance)
    effect_removed = Signal(object, object)  # (clip, EffectInstance)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clip = None
        self._effect_classes = get_available_effects()
        self._param_widgets = {}

        self.clip_label = QLabel()
        self.effects_list = QListWidget()
        for effect_class in self._effect_classes:
            self.effects_list.addItem(effect_class.get_name())

        self.params_form = QFormLayout()
        self.apply_button = QPushButton("Appliquer au clip")

        self.applied_list = QListWidget()
        self.remove_button = QPushButton("Retirer l'effet sélectionné")

        layout = QVBoxLayout(self)
        layout.addWidget(self.clip_label)
        layout.addWidget(QLabel("Effets disponibles"))
        layout.addWidget(self.effects_list, 1)
        layout.addLayout(self.params_form)
        layout.addWidget(self.apply_button)
        layout.addWidget(QLabel("Effets du clip"))
        layout.addWidget(self.applied_list, 1)
        layout.addWidget(self.remove_button)

        self.effects_list.currentRowChanged.connect(self._on_effect_chosen)
        self.apply_button.clicked.connect(self._apply_current_effect)
        self.remove_button.clicked.connect(self._remove_selected_effect)
        self.applied_list.currentRowChanged.connect(self._update_buttons)

        if self._effect_classes:
            self.effects_list.setCurrentRow(0)
        self.set_clip(None)

    # Définit le clip sélectionné (None si aucun). Branché sur TimelineWidget.clip_selected.
    @Slot(object)
    def set_clip(self, clip):
        self.clip = clip
        self.clip_label.setText("Clip sélectionné" if clip is not None else "Aucun clip sélectionné")
        self._refresh_applied_list()
        self._update_buttons()

    def _current_effect_class(self):
        row = self.effects_list.currentRow()
        return self._effect_classes[row] if 0 <= row < len(self._effect_classes) else None

    # Reconstruit le formulaire de paramètres de l'effet choisi
    def _on_effect_chosen(self, _row):
        while self.params_form.rowCount():
            self.params_form.removeRow(0)
        self._param_widgets = {}

        effect_class = self._current_effect_class()
        if effect_class is None:
            return
        for name, spec in effect_class.get_param_specs().items():
            widget = self._make_param_widget(spec)
            self._param_widgets[name] = widget
            self.params_form.addRow(spec.get("label", name), widget)
        self._update_buttons()

    @staticmethod
    def _make_param_widget(spec):
        param_type, default = spec["type"], spec["default"]
        if param_type is bool:
            widget = QCheckBox()
            widget.setChecked(default)
        elif param_type is int:
            widget = QSpinBox()
            widget.setRange(spec.get("min", -1_000_000), spec.get("max", 1_000_000))
            widget.setValue(default)
        elif param_type is float:
            widget = QDoubleSpinBox()
            widget.setRange(spec.get("min", -1e6), spec.get("max", 1e6))
            widget.setSingleStep(0.1)
            widget.setValue(default)
        else:
            widget = QLineEdit(str(default))
        return widget

    def _read_params(self):
        params = {}
        for name, widget in self._param_widgets.items():
            if isinstance(widget, QCheckBox):
                params[name] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                params[name] = widget.value()
            else:
                params[name] = widget.text()
        return params

    def _apply_current_effect(self):
        effect_class = self._current_effect_class()
        if self.clip is None or effect_class is None:
            return
        instance = EffectInstance(effect_class(), self._read_params())
        self.clip.add_effect(instance)
        self._refresh_applied_list()
        self.effect_applied.emit(self.clip, instance)

    def _remove_selected_effect(self):
        row = self.applied_list.currentRow()
        if self.clip is None or not 0 <= row < len(self.clip.get_effects()):
            return
        instance = self.clip.get_effects()[row]
        self.clip.remove_effect(instance)
        self._refresh_applied_list()
        self.effect_removed.emit(self.clip, instance)

    def _refresh_applied_list(self):
        self.applied_list.clear()
        if self.clip is not None:
            for instance in self.clip.get_effects():
                params = ", ".join(f"{k}={v}" for k, v in instance.get_params().items())
                self.applied_list.addItem(f"{instance.get_name()} ({params})")
        self._update_buttons()

    def _update_buttons(self, *_):
        self.apply_button.setEnabled(self.clip is not None and self._current_effect_class() is not None)
        self.remove_button.setEnabled(self.clip is not None and self.applied_list.currentRow() >= 0)
