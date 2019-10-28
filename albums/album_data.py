

# Stores paths to album's image files, for use on one system only
class AlbumData:
    def __init__(self, title, description='', paths=None):
        if paths is None:
            paths = []
        self.title = title
        self.paths = paths
        self.desc = description

    def add_path(self, path):
        self.paths.append(path)

    def get_paths(self):
        return self.paths

    def get_title(self):
        return self.title

    def get_description(self):
        return self.desc


# Stores raw image data to be used for transferring between systems
class FatAlbumData:
    def __init__(self, title, description='', images=None):
        if images is None:
            images = []
        self.title = title
        self.images = images
        self.desc = description

    def add_image(self, image):
        self.images.append(image)

    def get_images(self):
        return self.images

    def get_title(self):
        return self.title

    def get_description(self):
        return self.desc
