import scrapy
from scrapy.http import Request
from scrapy.utils.project import get_project_settings
from urllib.parse import urljoin
import re


class RestaurantsSpider(scrapy.Spider):
    name = 'restaurants'

    def __init__(self, category='', **kwargs):
        settings = get_project_settings()

        self.base_url = settings.get('BASE_URL')
        self.start_urls = [
            urljoin(self.base_url, settings.get('START_URL'))
        ]

        self.max_pages = settings.get('MAX_PAGES')

        super().__init__(**kwargs)

    def link(self, relative_path):
        return urljoin(self.base_url, relative_path)

    def parse(self, response):
        pagenum = response.meta['pagenum'] if 'pagenum' in response.meta else 1

        restaurants_selectors = response.css('div#EATERY_SEARCH_RESULTS div.listing')

        for selector in restaurants_selectors:
            restaurant = {}
            restaurant['url'] =  selector.css('div.title a.property_title::attr(href)').extract_first()
            restaurant['name'] = selector.css('div.title a.property_title::text').extract_first().strip()

            yield Request(url=self.link(restaurant['url']), meta={'restaurant': restaurant},
                          callback=self.parse_restaurant_page)

        next_page_url = response.css('''div#EATERY_LIST_CONTENTS div.unified.pagination
                                        a.nav.next::attr(href)''').extract_first()

        if next_page_url and (self.max_pages is None or pagenum < self.max_pages):
            yield Request(url=self.link(next_page_url),
                          meta={'pagenum': pagenum + 1},
                          callback=self.parse)

    def parse_restaurant_page(self, response):
        restaurant = response.meta['restaurant']

        restaurant['street_address'] = response.css('div#BODYCON div.address span.street-address::text')\
                                               .extract_first()
        restaurant['locality'] =       response.css('div#BODYCON div.address span.locality::text')\
                                               .extract_first()
        restaurant['country'] =        response.css('div#BODYCON div.address span.country-name::text')\
                                               .extract_first()

        try:
            rating_str = response.css('''span.header_rating
                                         span.ui_bubble_rating::attr(class)''').extract_first()
            restaurant['avg_rating'] = int(re.findall('bubble_[0-9]{2}', rating_str)[0][7:]) / 10.0

            numratings_str = response.css('''span.header_rating a.more span::text''').extract_first()
            restaurant['num_reviews'] = int(numratings_str)

        except (ValueError, TypeError, IndexError):
            restaurant['avg_rating'] = None
            restaurant['num_reviews'] = None

        try:
            restaurant['img'] = response.css('div.page_images')\
                                        .xpath('.//img[not(contains(@src, "x.gif"))]/@src').extract()[-1]
        except IndexError:
            pass

        reviews_page_url = response.css('''div#REVIEWS div.calloutReviewList
                                                    div.review-container div.quote a::attr(href)''')\
                                   .extract_first()
        restaurant['reviews'] = []

        if reviews_page_url:
            yield Request(url=self.link(reviews_page_url), meta={'restaurant': restaurant, 'pagenum': 1},
                          callback=self.parse_reviews)

    def parse_reviews(self, response):
        restaurant = response.meta['restaurant']
        pagenum = response.meta['pagenum']

        try:
            actual_pagenum = int(response.css('a.current::text').extract_first())
        except TypeError:
            actual_pagenum = 1

        if pagenum == 1 and actual_pagenum != 1:
            first_page_url = response.css('div.pageNumbers a.pageNum.first::attr(href)').extract_first()
            if first_page_url:
                yield Request(url=self.link(first_page_url), meta={'restaurant': restaurant, 'pagenum': 1},
                              callback=self.parse_reviews)
            return

        reviews_selectors = response.css('div#REVIEWS div.calloutReviewList div.reviewSelector')

        for selector in reviews_selectors:
            review = {}

            try:
                uid_str = selector.css('div.member_info div.memberOverlayLink::attr(id)').extract_first()
                review['uid'] = re.findall('UID_[0-9a-fA-F]*', uid_str)[0][4:]
            except (TypeError, IndexError):
                review['uid'] = None

            try:
                rating_str = selector.css('''div.reviewItemInline
                                            span.ui_bubble_rating::attr(class)''').extract_first()
                review['rating'] = int(re.findall('bubble_[0-9]{2}', rating_str)[0][7:]) / 10.0

            except (ValueError, TypeError, IndexError):
                review['rating'] = None

            review['title'] = selector.css('div.quote a span.noQuotes::text').extract_first()
            review['content'] = selector.css('div.entry p.partial_entry::text').extract_first()

            restaurant['reviews'].append(review)

        next_page_url = response.css('div#REVIEWS a.nav.next::attr(href)').extract_first()
        if next_page_url:
            yield Request(url=self.link(next_page_url),
                          meta={'restaurant': restaurant, 'pagenum': actual_pagenum + 1},
                          callback=self.parse_reviews)
        else:
            for key in restaurant.keys():
                try:
                    # Remove spaces and commas that tripadvisor sometimes insert
                    restaurant[key] = restaurant[key].strip(' ,')
                except AttributeError:
                    pass
            yield restaurant
