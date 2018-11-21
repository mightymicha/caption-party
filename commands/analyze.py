import sys
from helper import color, status, error
try:
    import click
except ImportError:
    sys.exit(error + """You need the following python packages:
            click""")


@click.command()
@click.argument('party', nargs=1)
def analyze(party, channels_resource):
    # Check input
    # Combine captions of each party
    print(status + "Analyzing: ", color.BOLD +
          color.BLUE + party.upper() + color.END)
