import json
import gradio as gr
from modules import ui, shared
from modules.ui import create_ui
from old_sd_firstpasser.tools import quote_swap, NAME


def create_setting_component(key, is_quicksettings=False):
    def fun():
        return opts.data[key] if key in opts.data else opts.data_labels[key].default

    info = opts.data_labels[key]
    t = type(info.default)
    args = (info.component_args() if callable(info.component_args) else info.component_args) or {}
    if info.component is not None:
        comp = info.component
    elif t == str:
        comp = gr.Textbox
    elif t == int:
        comp = gr.Number
    elif t == bool:
        comp = gr.Checkbox
    else:
        raise ValueError(f'bad options item type: {t} for key {key}')
    elem_id = f"setting_{key}"

    if not is_quicksettings:
        dirtyable_setting = gr.Group(elem_classes="dirtyable", visible=args.get("visible", True))
        dirtyable_setting.__enter__()
        dirty_indicator = gr.Button("", elem_classes="modification-indicator", elem_id="modification_indicator_" + key)

    if info.refresh is not None:
        if is_quicksettings:
            res = comp(label=info.label, value=fun(), elem_id=elem_id, **args)
            ui_common.create_refresh_button(res, info.refresh, info.component_args, f"refresh_{key}")
        else:
            with gr.Row():
                res = comp(label=info.label, value=fun(), elem_id=elem_id, **args)
                ui_common.create_refresh_button(res, info.refresh, info.component_args, f"refresh_{key}")
    elif info.folder is not None:
        with gr.Row():
            res = comp(label=info.label, value=fun(), elem_id=elem_id, elem_classes="folder-selector", **args)
            # ui_common.create_browse_button(res, f"folder_{key}")
    else:
        try:
            res = comp(label=info.label, value=fun(), elem_id=elem_id, **args)
        except Exception as e:
            log.error(f'Error creating setting: {key} {e}')
            res = None

    if res is not None and not is_quicksettings:
        res.change(fn=None, inputs=res, _js=f'(val) => markIfModified("{key}", val)')
        dirty_indicator.click(fn=lambda: getattr(opts, key), outputs=res, show_progress=False)
        dirtyable_setting.__exit__()

    return res


def makeUI(script):
    with gr.Row():
        firstpass_steps = gr.Slider(
            label='Firstpass steps',
            value=20,
            step=1,
            minimum=1,
            maximum=150,
            elem_id="firstpass_steps"
        )
        firstpass_denoising = gr.Slider(label='Firstpass denoising',
            value=0.55, elem_id="firstpass_denoising",
            minimum=0.0, maximum=1.0, step=0.01
        )
    with gr.Row():
        firstpass_upscaler = gr.Dropdown(
            value="ESRGAN_4x",
            choices=[x.name for x in shared.sd_upscalers],
            label="Firstpass upscaler",
            elem_id="firstpass_upscaler",
        )
    with gr.Row():
        sd_1_checkpoint = create_ui.create_setting_component('sd_model_checkpoint')
        sd_1_checkpoint.label = "Checkpoint for SD 1.x pass"

    def get_infotext_field(d, field):
        if NAME in d:
            return d[NAME].get(field)

    script.infotext_fields = [
        (firstpass_steps, lambda d: get_infotext_field(d, 'steps')),
        (firstpass_denoising, lambda d: get_infotext_field(d, 'denoising')),
        (firstpass_upscaler, lambda d: get_infotext_field(d, 'upscaler')),
        (sd_1_checkpoint, lambda d: get_infotext_field(d, 'model')),
    ]

    return [firstpass_steps, firstpass_denoising, firstpass_upscaler, sd_1_checkpoint]


def pares_infotext(infotext, params):
    try:
        params[NAME] = json.loads(params[NAME].translate(quote_swap))
    except Exception:
        pass
