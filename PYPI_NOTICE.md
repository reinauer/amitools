> **This is the final release of `amitools-amifuse`.** The package was a
> temporary fork of amitools that carried changes AmiFUSE needed before
> upstream had them. amitools 0.9.0 includes them, and AmiFUSE now depends
> on upstream amitools directly.
>
> Both distributions install the same `amitools` Python package, so remove
> the fork before installing upstream:
>
> ```bash
> pip uninstall amitools-amifuse
> pip install 'amitools[vamos]>=0.9.0'
> ```

