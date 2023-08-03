from _directory_gen import DirectoryGenerator
from _sync import live_directory_stats, live_compare_difference
import shutil
import sys
import time
import yaml
import textwrap


class PageTemplate:
    def __init__(self, content):
        self.content = content
    
    def copy(self):
        return PageTemplate(self.content)
    
    def replace(self, variable, value):
        self.content = self.content.replace("(" + variable + ")", str(value))
    
    def remove_line_with_if(self, variable, condition):
        match_start = "({})".format(variable)
        match_end = "(/{})".format(variable)
        matched_start_index = []
        matched_end_index = []
        for i, line in enumerate(self.content.split("\n")):
            if match_start in line:
                matched_start_index.append(i)
            
            if match_end in line:
                matched_end_index.append(i)
        
        if len(matched_start_index) != len(matched_end_index):
            print("Not same length")
            return
        
        content_lines = self.content.split("\n")
        if condition:
            for start, end in zip(matched_start_index, matched_end_index):
                del content_lines[start:end+1]
        else:
            line_indices_to_remove = matched_start_index + matched_end_index
            # From https://stackoverflow.com/a/11303234
            for index in sorted(line_indices_to_remove, reverse=True):
                del content_lines[index]
        self.content = "\n".join(content_lines)

    def __str__(self):
        return self.content


def generate_file(file_name: str, position: int, file_data: dict, **kwargs) -> str:
    """
    This function is the function to modify if you want to change how each file
    in the API is created. In this example, we are using the template (supplied
    by rebuild_api) and populating it with the information specific to each
    Endpoint.

    """
    api_template_directory = kwargs["api_template_directory"]
    template: PageTemplate = kwargs["template"].copy()

    class Parameter:
        def __init__(self, name, data_type, info, optional):
            self.name: str = name
            self.data_type: str = data_type
            self.info: str = info
            self.optional: bool = optional
        
        def __str__(self):
            extra = " **optional**" if self.optional else ""
            return "`{}`{} *{}*  \n{}\n".format(
                self.name, extra, self.data_type, self.info)
    
    # Create the parameters for each endpoint
    parameters = []
    if "parameters" in file_data:
        for name, fields in file_data["parameters"].items():
            parameters.append(Parameter(
                name,
                fields["type"],
                fields["info"],
                fields["optional"]
            ))
    
    # Load each file's footer
    footer_file = "{}/{}.mdx".format(api_template_directory, file_data["route"])
    try:
        with open(footer_file, encoding="utf8") as f:
            footer = f.read()
    except FileNotFoundError:
        footer = None

    # Let's begin extracting information for the template.
    route = file_data["route"]
    method = file_data["method"]
    privileged = file_data["privileged"]
    short = file_data["short"]
    description = file_data["description"]

    # Quick sanity check to make sure this is a valid endpoint. Otherwise, let's
    # not create it. Could also put a helpful print message to say it's been
    # ignored too.
    valid_methods = ["GET", "POST"]
    valid_types = ["string", "boolean", "integer"]
    if method not in valid_methods:
        return None # Don't create the file
    
    for parameter in parameters:
        parameter: Parameter
        if parameter.data_type not in valid_types:
            return None
    
    # ------------ Alright, let's populate the template then ------------
    # If the endpoint has no footer, don't print anything extra
    if footer is not None:
        template.replace("FOOTER", footer)
    else:
        template.replace("FOOTER", "")
    template.replace("SIDEBAR_POSITION", position)
    template.replace("METHOD", method)
    template.replace("ROUTE", route)

    # If the endpoint is not privileged, don't print anything extra
    template.remove_line_with_if("PRIVILEGED", not privileged)

    # If the endpoint has no input parameters, don't print anything extra
    if len(parameters) > 0:
        parameters_text = "\n".join([str(p) for p in parameters])
        template.replace("PARAMETERS", "## Parameters\n\n{}".format(parameters_text))
    else:
        template.replace("PARAMETERS", "")
    template.replace("DESCRIPTION", description)
    template.replace("SHORT", short)
    if method == "POST":
        template.replace("METHOD_COLOUR", "#FF6E26")
    else:
        template.replace("METHOD_COLOUR", "#46AF00")

    template.replace("SLUG", route.split("/")[-1])

    # If you want to add any extra values to the template then here is the
    # place to add them. All you need to do is add (CUSTOM_FIELD) to the
    # template.mdx

    # And then use:
    # template.replace("CUSTOM_FIELD", "My data")

    # -------------------------------------------------------------------

    return str(template)


class Config:
    def __init__(self, config):
        self.api_docs: str               = config["api_docs"]
        self.api_template_directory: str = config["api_template_directory"]
        self.api_template_file: str      = config["api_template_file"]
        self.api_build_to: str           = config["api_build_to"]
        self.api_section_label: str      = config["api_section_label"]


def rebuild_api(config: Config):
    """
    This function creates a DirectoryGenerator which is an internal representation
    of the file structure that is outlined in the docs.yaml file. Depending on the
    API and information you want to generate, you almost certainly may want to
    modify what information get passed to directory_generator.convert_to_model.
    """

    # Read the structure of the API so that the model can be based on this.
    try:
        with open(config.api_docs, encoding="utf8") as f:
            structure = yaml.safe_load(f.read())
    except FileNotFoundError:
        print("Docs '{}' does not exist".format(config.api_docs))
        return

    # Pass a template to the generation function so that each file create can
    # use it
    try:
        with open(config.api_template_file, encoding="utf8") as f:
            template = PageTemplate(f.read())
    except FileNotFoundError:
        print("Template '{}' does not exist".format(config.api_template_file))
        return

    # The function passed to convert_to_model, (in this case generate_file) will
    # be called for every file in the model. See the docstring for convert_to_model
    # for more information about the expected parameters for the function passed.
    directory_generator = DirectoryGenerator(structure, config.api_section_label)
    model = directory_generator.convert_to_model(
        generate_file,
        api_template_directory=config.api_template_directory,
        template=template
    )

    model.write_to_file(config.api_build_to)
    return model


def live_build(config: Config):
    """
    This function will regenerate the API whenever it notices a change in the
    template directory -> New file, removed file, or editted file.
    """
    old = live_directory_stats(config.api_template_directory)
    while True:
        time.sleep(1)
        _new = live_directory_stats(config.api_template_directory)
        removed_pages, modified_pages, added_pages = \
            live_compare_difference(old, _new)

        if len(removed_pages) + len(modified_pages) + len(added_pages) > 0:
            print("Updating")
            rebuild_api(config)
            old = _new


def main():
    if len(sys.argv) == 1:
        print("Usage: python gen.py [--build] [--clean] [--live] [--help]")
    
    if "--help" in sys.argv:
        print(textwrap.dedent("""
            Compiles the documentation in the Docusaurus format.
             --help       Displays this information and exits.
             --build      Compiles the documentation using the information
                          in config.yaml.
             --clean      Deletes the build directory and exits.
             --live       Runs with live compile. This implicitly begins a
                          build, but then whenever a change occurs in the
                          template directory or the api template directory,
                          the build directory is updated accordingly.
                          This allows you to have 'npm start' going in
                          another shell instance. This sometimes doesn't
                          work when an API page is removed. Running
                          'npm start' again will fix this.
            """
        ).strip("\n"))
        return

    try:
        with open("config.yaml") as f:
            config = Config(yaml.safe_load(f.read()))
    except FileNotFoundError:
        print("File 'config.yaml' does not exist")
        return
    
    # Deletes the build location
    if "--clean" in sys.argv:
        try:
            shutil.rmtree(config.api_build_to)
        except FileNotFoundError:
            pass
        print("Cleaned '{}'".format(config.api_build_to))
        return
    
    # Creates the API pages
    if "--build" in sys.argv:
        model = rebuild_api(config)
        print(f"Successfully generated {len(model)} pages")
    
    # Will update the API pages if it notices something change in the template
    # directory.
    if "--live" in sys.argv:
        try:
            live_build(config)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
