def add_to_viewer(viewer, name, data, type, **kwargs):
    try:
        viewer.layers[name].data = data
        viewer.layers[name].visible = True
    except KeyError:
        if type == "image":
            viewer.add_image(data, name=name, **kwargs)
        elif type == "labels":
            viewer.add_labels(data, name=name, **kwargs)
        elif type == "points":
            viewer.add_points(data, name=name, **kwargs)
        elif type == "tracks":
            viewer.add_tracks(data, name=name, **kwargs)
        elif type == "shapes":
            viewer.add_shapes(data, name=name, **kwargs)
        elif type == "surface":
            viewer.add_surface(data, name=name, **kwargs)
        elif type == "vectors":
            viewer.add_vectors(data, name=name, **kwargs)
        else:
            raise ValueError(f"Unknown type {type}")
