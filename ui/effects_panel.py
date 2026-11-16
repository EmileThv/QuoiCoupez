from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from core.clip import Clip
from effects.audio_effects import AUDIO_EFFECTS
from effects.base_effect import Effect
from effects.video_effects import VIDEO_EFFECTS

ERROR_STYLE = "border: 1px solid #e05050;"


# "Écho" -> "[Audio] Écho": audio effects are only heard in the exported video, not in the preview.
def _display_name(effect):
    prefix = "[Audio] " if effect.KIND == "audio" else ""
    return prefix + effect.NAME


# EffectsPanel: lists the available effects, the effects of the selected clip, and the
# parameters of the chosen effect. Every change is made on the clip and announced with
# effects_changed, so the preview can be updated during playback.
class EffectsPanel(QWidget):
    effects_changed = Signal(object)  # Clip whose effects (or their parameters) changed

    def __init__(self, available_effects=None, parent=None):
        super().__init__(parent)
        if available_effects is None:
            available_effects = VIDEO_EFFECTS + AUDIO_EFFECTS
        if not isinstance(available_effects, list):
            raise TypeError("effects_panel.__init__: available_effects must be a list")
        for effect_class in available_effects:
            if not (isinstance(effect_class, type) and issubclass(effect_class, Effect)):
                raise TypeError("effects_panel.__init__: available_effects must contain Effect subclasses")
        self.available_effects = available_effects
        self.clip = None

        self.title = QLabel()
        self.title.setWordWrap(True)

        self.effect_choice = QComboBox()
        for effect_class in available_effects:
            self.effect_choice.addItem(_display_name(effect_class), effect_class)
        self.add_button = QPushButton("Ajouter")
        self.add_button.clicked.connect(self._add_effect)
        add_row = QHBoxLayout()
        add_row.addWidget(self.effect_choice, 1)
        add_row.addWidget(self.add_button)

        self.effect_list = QListWidget()
        self.effect_list.currentRowChanged.connect(self._show_params)
        self.remove_button = QPushButton("Retirer")
        self.remove_button.clicked.connect(self._remove_effect)

        self.params_title = QLabel()
        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        self.params_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(add_row)
        layout.addWidget(QLabel("Effets du clip (appliqués dans l'ordre) :"))
        layout.addWidget(self.effect_list, 1)
        layout.addWidget(self.remove_button)
        layout.addWidget(self.params_title)
        layout.addWidget(self.params_widget)
        layout.addStretch()

        self.set_clip(None)

    # Shows the effects of the given clip (None: nothing selected, the panel is disabled)
    def set_clip(self, clip):
        if clip is not None and not isinstance(clip, Clip):
            raise TypeError("effects_panel.set_clip: clip must be of type core.clip.Clip or None")
        self.clip = clip
        enabled = clip is not None
        self.effect_choice.setEnabled(enabled)
        self.add_button.setEnabled(enabled)
        self.effect_list.setEnabled(enabled)
        if clip is None:
            self.title.setText("Sélectionnez un clip sur la timeline pour lui ajouter des effets.")
        else:
            self.title.setText(f"<b>Effets de : {clip.get_source().get_name()}</b>")
        self._refresh_list()

    def get_clip(self):
        return self.clip

    def _refresh_list(self, selected_row=None):
        self.effect_list.blockSignals(True)
        self.effect_list.clear()
        if self.clip is not None:
            for effect in self.clip.get_effects():
                item = QListWidgetItem(_display_name(effect))
                item.setData(Qt.UserRole, effect)
                self.effect_list.addItem(item)
        self.effect_list.blockSignals(False)

        count = self.effect_list.count()
        if selected_row is None:
            selected_row = count - 1
        self.effect_list.setCurrentRow(min(selected_row, count - 1))
        self._show_params(self.effect_list.currentRow())

    def _selected_effect(self):
        item = self.effect_list.currentItem()
        return item.data(Qt.UserRole) if item is not None else None

    def _add_effect(self):
        if self.clip is None:
            return
        effect_class = self.effect_choice.currentData()
        self.clip.add_effect(effect_class())
        self._refresh_list()
        self.effects_changed.emit(self.clip)

    def _remove_effect(self):
        effect = self._selected_effect()
        if self.clip is None or effect is None:
            return
        row = self.effect_list.currentRow()
        self.clip.remove_effect(effect)
        self._refresh_list(row)
        self.effects_changed.emit(self.clip)

    # Builds one editor per parameter of the selected effect
    def _show_params(self, row):
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)

        effect = self._selected_effect()
        self.remove_button.setEnabled(effect is not None)
        if effect is None:
            self.params_title.setText("")
            return
        self.params_title.setText(f"<b>Paramètres : {effect.get_name()}</b>")

        values = effect.get_params()
        for name, spec in effect.PARAMS.items():
            editor = self._make_editor(effect, name, spec, values[name])
            self.params_layout.addRow(spec.get("label", name), editor)

    def _make_editor(self, effect, name, spec, value):
        if spec["type"] is int:
            editor = QSpinBox()
            editor.setRange(spec.get("min", -1_000_000), spec.get("max", 1_000_000))
            editor.setValue(value)
            editor.valueChanged.connect(lambda v: self._set_param(effect, name, v, editor))
            return editor

        if spec["type"] is float:
            editor = QDoubleSpinBox()
            minimum = spec.get("min", -1_000_000.0)
            maximum = spec.get("max", 1_000_000.0)
            editor.setRange(minimum, maximum)
            editor.setDecimals(2)
            editor.setSingleStep(0.01 if maximum - minimum <= 1 else 0.1 if maximum - minimum <= 10 else 1)
            editor.setValue(value)
            editor.valueChanged.connect(lambda v: self._set_param(effect, name, v, editor))
            return editor

        line_edit = QLineEdit(value)
        line_edit.textEdited.connect(lambda text: self._set_param(effect, name, text, line_edit))
        kind = spec.get("kind")
        if kind not in ("color", "file"):
            return line_edit

        button = QPushButton("…")
        button.setFixedWidth(28)
        if kind == "color":
            button.clicked.connect(lambda: self._pick_color(effect, name, line_edit))
        else:
            button.clicked.connect(lambda: self._pick_file(effect, name, line_edit))
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(line_edit, 1)
        row.addWidget(button)
        return container

    def _pick_color(self, effect, name, line_edit):
        color = QColorDialog.getColor(QColor(line_edit.text()), self, "Couleur")
        if color.isValid():
            line_edit.setText(color.name().upper())
            self._set_param(effect, name, line_edit.text(), line_edit)

    def _pick_file(self, effect, name, line_edit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir une image", line_edit.text(), "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            line_edit.setText(path)
            self._set_param(effect, name, path, line_edit)

    # An invalid value (wrong color...) is not given to the effect: the field turns red instead.
    def _set_param(self, effect, name, value, editor):
        try:
            effect.set_param(name, value)
        except (TypeError, ValueError) as error:
            editor.setStyleSheet(ERROR_STYLE)
            editor.setToolTip(str(error))
            return
        editor.setStyleSheet("")
        editor.setToolTip("")
        self.effects_changed.emit(self.clip)
