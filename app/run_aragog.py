import click

from aragog import Aragog


@click.command()
@click.option('--domain', default='www.thomann.de/', help='The root of the website you want to crawl')
@click.option('--schema', default='https://', help='The url schema (http:// or https://)')
@click.option('--plot_output', is_flag=True, default=False, help='Dump the crawled domain in images')
def main(domain: str, schema: str, plot_output: bool) -> None:
    if not domain.endswith('/'):
        print(f"Warning: {domain} doesn't point explicitly to a root path, using {domain + '/'} instead.")
        domain += '/'
    if schema not in ('http://', 'https://'):
        raise NotImplementedError(f'{schema} is not a supported schema, try http:// or https://')

    aragog = Aragog(website_domain=domain, schema=schema, plot_output=plot_output)
    aragog.crawl()


if __name__ == '__main__':
    main()
