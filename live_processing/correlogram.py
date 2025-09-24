# correlogram.py
import tkinter.ttk as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import tkinter as tk

# Match your project structure
from ui.two_page_wizard import WizardResult, open_two_page_wizard
from ui.ui_utils import center_window


# ----------------------------- Tk Figure Window -----------------------------

def show_correlogram_window(parent: tk.Misc, fig, title: str):
    """
    Embed a Matplotlib Figure in its own persistent Tk Toplevel, parented to the app root.
    Centers the window on screen.
    """
    root = parent.winfo_toplevel() if isinstance(parent, tk.Misc) else None

    win = tk.Toplevel(master=root)
    win.title(title)

    container = tk.Frame(win)
    container.pack(fill="both", expand=True)

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    toolbar = NavigationToolbar2Tk(canvas, container)
    toolbar.update()
    toolbar.pack(fill="x")

    # keep refs so they don’t get garbage collected
    win._canvas = canvas
    win._toolbar = toolbar
    win._fig = fig

    def _on_close():
        try:
            import matplotlib.pyplot as _plt
            _plt.close(fig)
        except Exception:
            pass
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _on_close)

    # --- Center on screen ---
    # Let widgets compute their natural size, then center to that size
    win.update_idletasks()
    width = max(900, win.winfo_reqwidth())    # ensure a reasonable minimum width
    height = max(650, win.winfo_reqheight())  # ensure a reasonable minimum height
    center_window(win, width, height)

    return win


def ask_correlogram_options(parent: tk.Misc, *, ds1: str, ds2: str):
    """
    Modal dialog to pick plot options right after the wizard finishes.
    Centers itself on screen before showing.
    Returns a dict like:
      { 'normalize': 'none'|'row'|'col'|'all',
        'cmap': str,
        'annotate': bool,
        'zero_diag': bool,
        'title': str }
    or None if cancelled.
    """
    root = parent.winfo_toplevel() if isinstance(parent, tk.Misc) else None

    win = tk.Toplevel(master=root)
    win.title("Correlogram Options")
    win.transient(root)
    win.grab_set()

    # Defaults
    normalize_var = tk.StringVar(value="none")
    cmap_var = tk.StringVar(value="Blues")
    annotate_var = tk.BooleanVar(value=True)
    zero_diag_var = tk.BooleanVar(value=False)
    title_var = tk.StringVar(value=f"Correlogram: {ds1} × {ds2}")

    # Common colormaps
    cmaps = [
        "Blues", "Reds", "Greens", "Purples", "Oranges", "Greys",
        "viridis", "plasma", "inferno", "magma", "cividis",
        "coolwarm", "Spectral", "YlGnBu", "YlOrRd", "PuBuGn"
    ]

    # Layout
    frm = ttk.Frame(win, padding=12)
    frm.pack(fill="both", expand=True)

    # Title
    ttk.Label(frm, text="Title:").grid(row=0, column=0, sticky="w", padx=(0,8), pady=(0,8))
    title_entry = ttk.Entry(frm, textvariable=title_var, width=48)
    title_entry.grid(row=0, column=1, sticky="ew", pady=(0,8))

    # Normalize
    ttk.Label(frm, text="Normalize:").grid(row=1, column=0, sticky="w", padx=(0,8), pady=4)
    normalize_combo = ttk.Combobox(frm, textvariable=normalize_var, values=["none", "row", "col", "all"], state="readonly", width=12)
    normalize_combo.grid(row=1, column=1, sticky="w", pady=4)

    # Colormap
    ttk.Label(frm, text="Colormap:").grid(row=2, column=0, sticky="w", padx=(0,8), pady=4)
    cmap_combo = ttk.Combobox(frm, textvariable=cmap_var, values=cmaps, state="readonly", width=20)
    cmap_combo.grid(row=2, column=1, sticky="w", pady=4)

    # Checkboxes
    annotate_chk = ttk.Checkbutton(frm, text="Annotate cells", variable=annotate_var)
    annotate_chk.grid(row=3, column=1, sticky="w", pady=4)

    zero_diag_chk = ttk.Checkbutton(frm, text="Zero-out diagonal", variable=zero_diag_var)
    zero_diag_chk.grid(row=4, column=1, sticky="w", pady=4)

    # Buttons
    btns = ttk.Frame(frm)
    btns.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12,0))
    result = {"_ok": False}

    def on_ok():
        result.update({
            "_ok": True,
            "normalize": normalize_var.get(),
            "cmap": cmap_var.get(),
            "annotate": bool(annotate_var.get()),
            "zero_diag": bool(zero_diag_var.get()),
            "title": title_var.get().strip() or f"Correlogram: {ds1} × {ds2}",
        })
        win.destroy()

    def on_cancel():
        result["_ok"] = False
        win.destroy()

    ttk.Button(btns, text="Cancel", command=on_cancel).pack(side="right", padx=(0,8))
    ttk.Button(btns, text="OK", command=on_ok).pack(side="right")

    # Sizing and focus
    frm.columnconfigure(1, weight=1)
    title_entry.focus_set()

    # --- Center on screen ---
    win.update_idletasks()
    # Use the natural requested size, but ensure a sensible minimum
    width = max(520, win.winfo_reqwidth())
    height = max(240, win.winfo_reqheight())
    center_window(win, width, height)

    # Modal behavior
    win.protocol("WM_DELETE_WINDOW", on_cancel)
    win.wait_visibility()
    win.wait_window()

    return result if result.get("_ok") else None


# ----------------------------- Plotting -----------------------------

def plot_label_correlogram(
    df: pd.DataFrame,
    *,
    col_y: str,                     # dataset 1 name (y-axis)
    col_x: str,                     # dataset 2 name (x-axis)
    weight: str = "count",          # "count" (kept for parity)
    normalize: str = "row",        # "none" | "row" | "col" | "all"
    cmap: str = "Blues",
    annotate: bool = True,
    zero_diag: bool = False,        # set True to zero-out perfect matches on the diagonal
    title: str | None = None,
):
    """
    Plot a correlogram (co-occurrence heatmap) between two categorical columns.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: 'text', col_y, col_x.
    col_y : str
        Column name for Y axis (Dataset 1 label column).
    col_x : str
        Column name for X axis (Dataset 2 label column).
    weight : {"count"}, default "count"
        - "count": cell value = number of rows with (col_y, col_x)
    normalize : {"none", "row", "col", "all"}, default "none"
        - "row": each row sums to 1
        - "col": each column sums to 1
        - "all": divide by grand total
        - "none": raw counts
    cmap : str, default "Blues"
        Matplotlib colormap name.
    annotate : bool, default True
        Draw numeric labels on each cell.
    zero_diag : bool, default False
        If True, sets the diagonal to zero before normalization/plotting.
    title : str or None
        Optional plot title.

    Returns
    -------
    fig, ax : matplotlib Figure and Axes
    """

    required_cols = {"text", col_y, col_x}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {sorted(missing)}")

    # Work on a copy to avoid modifying the caller's df
    data = df.copy()

    # Ensure labels are strings (prevents issues with None/NaN vs. ints)
    data[col_y] = data[col_y].astype(str)
    data[col_x] = data[col_x].astype(str)

    # Axis order: alphabetical by default (stable and predictable)
    y_order = sorted(pd.unique(data[col_y]))
    x_order = sorted(pd.unique(data[col_x]))

    # Build the matrix (counts)
    mat = pd.crosstab(
        index=pd.Categorical(data[col_y], categories=y_order, ordered=True),
        columns=pd.Categorical(data[col_x], categories=x_order, ordered=True),
    ).reindex(index=y_order, columns=x_order, fill_value=0)

    # Optionally zero the diagonal (useful if you only care about cross-label associations)
    if zero_diag:
        common = set(mat.index).intersection(mat.columns)
        for k in common:
            mat.loc[k, k] = 0

    # Normalize as requested
    mat_values = mat.to_numpy(dtype=float)
    if normalize == "row":
        row_sums = mat_values.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        mat_plot = mat_values / row_sums
        fmt = ".2f"
    elif normalize == "col":
        col_sums = mat_values.sum(axis=0, keepdims=True)
        col_sums[col_sums == 0] = 1.0
        mat_plot = mat_values / col_sums
        fmt = ".2f"
    elif normalize == "all":
        total = mat_values.sum()
        total = total if total != 0 else 1.0
        mat_plot = mat_values / total
        fmt = ".3f"
    elif normalize == "none":
        mat_plot = mat_values
        fmt = ".0f"
    else:
        raise ValueError("normalize must be one of {'none','row','col','all'}")

    # Plot (size scales with label cardinality)
    fig_w = max(6, len(x_order) * 0.5 + 2)
    fig_h = max(5, len(y_order) * 0.5 + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(mat_plot, aspect="auto", cmap=cmap)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.ax.yaxis.set_major_locator(MaxNLocator(6))
    cbar.ax.set_ylabel(
        "Value" + (f" ({normalize}-normalized)" if normalize != "none" else ""),
        rotation=-90, va="bottom"
    )

    # Ticks & labels
    ax.set_xticks(np.arange(len(x_order)))
    ax.set_yticks(np.arange(len(y_order)))
    ax.set_xticklabels(x_order, rotation=45, ha="right")
    ax.set_yticklabels(y_order)

    # Grid lines
    ax.set_xticks(np.arange(-.5, len(x_order), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(y_order), 1), minor=True)
    ax.grid(which="minor", color="w", linestyle="-", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Annotations
    if annotate:
        vmax = np.nanmax(mat_plot) if mat_plot.size else 0
        threshold = vmax * 0.6 if vmax > 0 else 0
        for i in range(len(y_order)):
            for j in range(len(x_order)):
                val = mat_plot[i, j]
                txt_color = "white" if val >= threshold and vmax > 0 else "black"
                ax.text(j, i, f"{val:{fmt}}", ha="center", va="center", fontsize=9, color=txt_color)

    ax.set_xlabel(col_x)
    ax.set_ylabel(col_y)
    if title is None:
        base = "count" if weight == "count" else weight
        norm = "" if normalize == "none" else f" ({normalize}-normalized)"
        title = f"Correlogram of {col_y} × {col_x} — {base}{norm}"
    ax.set_title(title)
    fig.tight_layout()

    # Give the native window a nice title (helps when multiple figures are open)
    try:
        fig.canvas.manager.set_window_title(title)
    except Exception:
        pass

    return fig, ax


# ----------------------------- Public Entry (Wizard) -----------------------------

def open_correlogram_wizard(parent: tk.Misc):
    """
    Opens the reusable two-page wizard and, on finish, prompts for plot options
    and then renders the correlogram in a persistent Tk window.
    Mirrors the usage pattern in reliability_calculator.
    """

    def _finish_handler(*args):
        # Accept either signature: (res) or (res, win)
        if not args:
            return False
        res: WizardResult = args[0]
        host_parent = parent

        # Validate expected fields from the wizard
        try:
            merged = res.merged.copy()
            ds1 = res.ds1_name
            ds2 = res.ds2_name
        except Exception:
            from tkinter import messagebox
            messagebox.showerror("Wizard Error", "Unexpected wizard result payload.", parent=host_parent)
            return False

        if "text" not in merged.columns or ds1 not in merged.columns or ds2 not in merged.columns:
            from tkinter import messagebox
            messagebox.showerror(
                "Data Error",
                f"Merged dataframe is missing required columns. Need: 'text', '{ds1}', '{ds2}'.",
                parent=host_parent
            )
            return False

        # === NEW: Ask user for plotting options ===
        opts = ask_correlogram_options(host_parent, ds1=ds1, ds2=ds2)
        if opts is None:
            # User cancelled the options dialog; do not open the correlogram window.
            return False

        # Build figure with chosen options
        fig, _ = plot_label_correlogram(
            merged,
            col_y=ds1,
            col_x=ds2,
            weight="count",
            normalize=opts["normalize"],
            cmap=opts["cmap"],
            annotate=opts["annotate"],
            zero_diag=opts["zero_diag"],
            title=opts["title"],
        )

        # Show in persistent Tk window (no plt.show())
        show_correlogram_window(parent=host_parent, fig=fig, title=opts["title"])

        # Return True so wizards that expect a truthy value will close.
        return True

    # Launch the wizard; our finish handler handles options + plotting.
    return open_two_page_wizard(parent, on_finish=_finish_handler)
