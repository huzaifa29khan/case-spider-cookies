import scrapy

class BasicSpider(scrapy.Spider):
    name = "basic"
    allowed_domains = ["epublic-access.riverside.courts.ca.gov"]

    start_case = 3145926
    end_case = 3145945

    custom_settings = {
        'COOKIES_ENABLED': True,
        'COOKIES_DEBUG': True,
    }

    cookies = {
        'has_js': '1',
        'SSESS5dcaf0b317a9ed2ebdfcbc4d2c83708b': 'qpnhZe7Rbfj5KxSDfv5vL2d_QR5GgXw7NPq4hD83FnI',
        'AWSALB': '5ebjr1wJtWitoRZVfhz68H5wYOGnCJobTJ2whAu8HHSC1+wG7YKmUgt7Q5Dih78zqJJgqfeqfIlYTBtm1GxmYHOeKPxHbtRtaJ15khJwf9jde/8BylrpeU1ummCP',
        'AWSALBCORS': '5ebjr1wJtWitoRZVfhz68H5wYOGnCJobTJ2whAu8HHSC1+wG7YKmUgt7Q5Dih78zqJJgqfeqfIlYTBtm1GxmYHOeKPxHbtRtaJ15khJwf9jde/8BylrpeU1ummCP'
    }

    def start_requests(self):
        url = f"https://epublic-access.riverside.courts.ca.gov/public-portal/?q=node/385/{self.start_case}"
        yield scrapy.Request(url=url, cookies=self.cookies, callback=self.parse, meta={'case_num': self.start_case})

    def parse(self, response):
        case_num = response.meta['case_num']
        self.logger.info(f"Processing case number: {case_num}")

        case_id = response.css('td[style*="color: #CC0000; font-size:18px;"] b::text').get()

        if case_id:
            panel = response.xpath(
                "//a[.//span and contains(normalize-space(string(.//span)),'PARTIES')]/ancestor::div[contains(@class,'formPanel')][1]"
            )
            rows = panel.xpath(".//table[contains(@id,'tree_table')]/tbody/tr")

            parties = []
            for r in rows:
                name = " ".join(r.xpath(".//td[2]//text()").getall()).strip()
                role = " ".join(r.xpath(".//td[3]//text()").getall()).strip()
                if name:
                    parties.append((name, role))

            output = {
                'case_number': case_id.strip(),
                'filed_date': (response.xpath('//td[contains(text(), "Filed Date:")]/following-sibling::td[1]/text()').get() or "").strip(),
                'case_status': (response.xpath('//td[contains(text(), "Case Status:")]/following-sibling::td[1]/text()').get() or "").strip(),
                'description': (response.css('td[style*="text-align: center; font-size:18px;"]::text').get() or "").strip(),
                'case_type': (response.css('td[style*="text-align: center; overflow-wrap: normal;"] b::text').get() or "").strip(),
            }

            for idx, (n, s) in enumerate(parties, start=1):
                output[f'party_name{idx}'] = n
                output[f'party{idx}_role'] = s

            yield output
        else:
            self.logger.info(f"No valid page found for case number {case_num}")

        next_case = case_num + 1
        if next_case <= self.end_case:
            next_url = f"https://epublic-access.riverside.courts.ca.gov/public-portal/?q=node/385/{next_case}"
            yield scrapy.Request(url=next_url, cookies=self.cookies, callback=self.parse, meta={'case_num': next_case})
        else:
            self.logger.info(f"Reached end of range ({self.end_case}). Stopping spider.")
