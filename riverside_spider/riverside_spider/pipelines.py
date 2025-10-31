# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import re
from datetime import datetime

class CleanPipeline:
    DATE_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")

    def _collapse(self, s):
        return "" if not s else " ".join(s.split())

    def _title(self, s):
        return s.title() if s else ""

    def _to_iso_date(self, s):
        if not s:
            return ""
        m = self.DATE_RE.search(s)
        if not m:
            return ""
        try:
            return datetime.strptime(m.group(1), "%m/%d/%Y").strftime("%Y-%m-%d")
        except Exception:
            return m.group(1)

    def process_item(self, item, spider):
        out = {}
        out["Case Number"] = self._collapse(item.get("case_number", ""))
        out["Filed Date"] = self._to_iso_date(item.get("filed_date", ""))
        out["Case Type"] = self._title(self._collapse(item.get("case_type", "")))
        out["Status"] = self._title(self._collapse(item.get("case_status", "")))
        out["Description"] = self._title(self._collapse(item.get("description", "")))

        # Collect parties (skip role "Judge"), produce Party1/Party2 ...
        p = 1
        for i in range(1, 6):  # change 6 -> larger number if you expect more parties
            name = self._title(self._collapse(item.get(f"party_name{i}", "")))
            role = self._title(self._collapse(item.get(f"party{i}_role", "")))
            if not name:
                continue
            if role.lower() == "judge":
                continue
            out[f"Party{p} Name"] = name
            out[f"Party{p} Type"] = role
            p += 1

        return out


class RiversideSpiderPipeline:
    def process_item(self, item, spider):
        return item
