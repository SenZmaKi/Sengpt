<h1 align="center">
 Sengpt
</h1>
<p align="center">
  ChatGPT in your terminal, runs on  
  <a href="https://github.com/Zai-Kun/reverse-engineered-chatgpt">re-gpt</a> so no OpenAI API key required
</p>
<p align="center">
<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#usage">Usage</a> •
  <a href="#building-from-source">Building from source</a>
</p>

## Installation

Ensure you have [Python 3.11](https://www.python.org/downloads/release/python-3111) and [Glow](https://github.com/charmbracelet/glow) installed.

```bash
pip install sengpt
```

## Configuration

### Session token

- Go to https://chat.openai.com and log in or sign up.
- Open the browser developer tools (right click and click "inspect" or "inspect element").
- Go to the Application tab (try expanding the dev tools window if you can't find it) and expand the Cookies section.
- Look for https://chat.openai.com.
- Copy the value for \_\_Secure-next-auth.session-token.
- Run `sengpt --session_token <your-session-token-goes-here>`.

### Preconfigured prompts

- Open the config file, run `sengpt --config_file` to see it's location.
- Add a field named `preconfigured_prompts` and set it's value to key value pairs of prompt name and value e.g.,

```json
{
  "preconfigured_prompts": {
    "readme": "generate a README.md for this project",
    "expain": "briefly explain what this code does",
    "refactor": "refactor this code to improve readability"
  }
}
```

- To pass the prompt run `sengpt --prompt_name` or `sengpt -pn`.
- Warning!!! Make sure the short version of the prompt name doesn't clash with each other or with any of sengpt's default flags, i.e., a prompt name like `script_tags` will clash with `session_token` so every time you try and use it sengpt will think you want to set your session token.
- The preconfigured prompts are appended to the final prompt i.e., `some_project.py | sengpt --readme make it as brief as possible`

### Modes

#### Interactive mode

Back and forth interaction with ChatGPT, saves the conversation on exit.

Currently doesn't support piped inputs i.e., `cat README.md | sengpt summarise this document`, if piped inputs are passed Query mode will be used instead.

Press `Ctrl + C` to exit.

#### Query mode

Print ChatGPT's response, delete the conversation and exit.

#### Default mode

The default mode is interactive mode but you can change this in the config

```json
{
  "default_mode": "query"
}
```

With this configuration to use interactive mode run `sengpt --interactive`

### Models

Either `gpt-3.5` or `gpt-4` can be used, the default is `gpt-3.5`. `gpt-4` requires a ChatGPT Plus account and is slower. To switch to `gpt-4` add this in your config file.

```json
{
  "model": "gpt-4"
}
```

### Username
How your username appears in the conversation, the default is `You`.
```json
{
  "username": "Sen"
}
```

## Usage

```

Usage: sengpt [prompt] [options]

-h, --help Show help message and exit
-v, --version Show the version information
-cf, --config_file Show the config file's contents and location
-st, --session_token Set session token

-ng, --no_glow Disable pretty printing with Glow,
this can be set to be the default behaviour in the config file

-c, --copy Copy the prompt response to the clipboard,
this can be set to be the default behaviour in the config file

-p, --paste Append the most recently copied clipboard text to the sent prompt
-rc, --recent_conversation Use the most recently saved conversation as context
-pp, --preconfigured_prompt Append a preconfigured prompt to the sent prompt,
replace "preconfigured_prompt" with the prompt's name
as it appears in the config file

-q, query Use query mode i.e., print ChatGPT's response and exit,
this flag is only necessary if "default_mode" in config file is interactive

-s, --save By default conversations in query mode are deleted on exit,
this saves the conversation instead,
this can be set to be the default behaviour in the config file

-i, --interactive Use interactive mode i.e., back and forth interaction with ChatGPT,
this flag is only necessary if "default_mode" in the config file is query

-d, --delete By default conversations in interactive mode are saved on exit,
this deletes then exits the interactive mode session,
this can be set to be the default behaviour in the config file

```

## Building from Source

Ensure you have [Python 3.11](https://www.python.org/downloads/release/python-3111) and [Git](https://github.com/git-guides/install-git) installed.

1. **Set everything up.**

```
git clone https://github.com/SenZmaKi/Sengpt && cd Sengpt && pip install poetry && poetry install
```

2. **Run Sengpt.**

```
poetry run sengpt
```

3. **Build the package to install with pip**.

```
poetry build
```

- The `tar` and `wheel` will be built at `Sengpt/dist`
