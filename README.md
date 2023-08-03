# API Generator

This helper repository converts a `.yaml` file containing API definitions, into actual MDX files. The default is great for use with Docusaurus.

## Format

Imagine you want the structure:

```txt
📂api
┗ 📂player
  ┣ 📂inventory
  ┃ ┣ 📜add.mdx
  ┃ ┗ 📜remove.mdx
  ┗ 📂game
    ┣ 📂management
    ┃ ┣ 📜start.mdx
    ┃ ┗ 📜end.mdx
    ┗ 📂stats
      ┣ 📜overall.mdx
      ┗ 📜win_loss.mdx
```

(This is exactly how this current repository is setup)

Then the yaml would look like this:

```yaml
---
player:
  sidebar: Player
  files:
  - inventory.mdx:
      sidebar: Inventory
      files:
      - add.mdx:
      - remove.mdx:
  - health.mdx:
  - edit_health.mdx:
game:
  sidebar: Game
  files:
  - management:
      sidebar: Management
      files:
      - start.mdx:
      - end.mdx:
  - stats:
      sidebar: Statistics
      files:
      - overall.mdx:
      - win_loss.mdx:
```

So the format is roughly:

```yaml
folder:
  sidebar: Name of the folder in the sidebar
  files:
  - name_of_file:
      extra_data: Can be anything
      extra_data2: Can be anything
  - name_of_folder:
      sidebar: Nested folder
      files:
      - ...
```

This format is recursive. The way the format knows if a "file" is actually a folder, is if the key `files` is inside it. So when adding extra information for each file, don't use the key `files`.

## Config

The next most important file is the `config.yaml`. This file needs to be in your working directory. This is an example of the file:

```yaml
---
api_docs: example_docs_layout.yaml
api_template_directory: ../templates
api_template_file: ../templates/base_page_template.mdx
api_build_to: ../demo
api_section_label: My Game Endpoints
```

This file contains information critical for `gen.py` to do its job. I believe these are fairly self-explanitory in this repository. The only thing to take note of here is that `api_build_to` is **deleted** when `python gen.py --clean` is called. So be careful.

## Running

Running `python gen.py` will give you more information, but a typical user would probably write:

```bash
cd src
```

```bash
python gen.py --build
```

Of course, making sure that the `config.yaml` is in your working directory and is pointing to files/folders relative to your working directory: eg:

```bash
$ python src/gen.py
Usage: python gen.py [--build] [--clean] [--live] [--help]
File 'config.yaml' does not exist
```

As you can see it expected the `config.yaml` file to exist in the same directory.
