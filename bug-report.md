
In `schema.py`:
```python
    # hanyu: add this function to dump the noise model (so that we can load it later)
    # will be called in QuEraSimulationResult to_json
    # will be loaded in `noise_model = NoiseModel(**json["noise_model"])`
    def model_dump(self, mode: str = "json"):
        """Dump the noise model for later reloading.

        Args:
            mode (str): The output format. "json" returns a JSON string,
                        "dict" returns a dictionary. Default is "json".

        Returns:
            Union[str, dict]: The dumped noise model data.
        """
        data = self.dict()
        if mode == "json":
            return data
        else:
            raise ValueError("Unsupported mode. Please choose 'json' or 'dict'.")
```

