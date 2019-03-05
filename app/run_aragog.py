import click

from aragog import Aragog


@click.command()
@click.option('--domain', default='www.thomann.de/', help='The root of the website you want to crawl')
@click.option('--schema', default='https://', help='The url schema (http:// or https://)')
@click.option('--plot_output', is_flag=True, default=False, help='Dump the crawled domain in images')
def main(domain, schema, plot_output):
    aragog = Aragog(website_domain=domain, schema=schema, plot_output=plot_output)
    aragog.crawl()


if __name__ == '__main__':
    main()
