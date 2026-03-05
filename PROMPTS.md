Read ./dictionary.json. This is a dictionary file used to map common technical typos in closed caption files to what should actually be displayed in the closed caption text. For example, a text-to-speech engine might produce the text "dev you random" as a result of pronounciation, but this is a technical typo in the context of a closed caption file as the closed caption should instead display "/dev/urandom".

Write a python3 file called "main.py" that reads in the "dictionary.json" file in the same directory, returning a user friendly error if the file is not found or is of invalid format. Then, verify that the user provided exactly one argument to main.py. This argument can either be a file or a directory. If it is a file, verify it ends with a ".vtt" extension, reporting a user friendly error if invalid. If it is a directory, then recursively scan that directory and collect an array of all .vtt files found.

For each vtt file:
- print its absolute path to console
- read the vtt file and tokenize
- for each token in the file that matches an "mistake" (ex: "dev you random"), replace it with the value of "replace_with"
- overwrite the vtt file with the changes

at the end of your run, summarize the number of files changed, the number of mistakes corrected, and provide a table illustrating the frequency in which each mistake was identified.

