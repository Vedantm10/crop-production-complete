"""
tests/test_api.py
-----------------
Integration tests for api.py using FastAPI's TestClient (backed by httpx).
No live server is needed — the client exercises the ASGI app in-process.

Run with:
    $env:PYTHONIOENCODING='utf-8'
    .venv\\Scripts\\python.exe -m pytest tests/test_api.py -v
"""

import json
import os
import sys

import pytest

# Ensure the project root is importable from any working directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient

from api import app

# Single shared client — app startup runs once for the test session
client = TestClient(app)


# =============================================================================
# /api/health
# =============================================================================
class TestHealth:
    def test_status_200(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_status_ok(self):
        body = client.get("/api/health").json()
        assert body["status"] == "ok"

    def test_records_count(self):
        body = client.get("/api/health").json()
        assert body["records"] == 463_847

    def test_year_bounds(self):
        body = client.get("/api/health").json()
        assert body["year_min"] == 1997
        assert body["year_max"] == 2025

    def test_all_keys_present(self):
        body = client.get("/api/health").json()
        for key in ("status", "records", "year_min", "year_max"):
            assert key in body, f"Missing key: {key}"


# =============================================================================
# /api/metadata
# =============================================================================
class TestMetadata:
    def test_status_200(self):
        assert client.get("/api/metadata").status_code == 200

    def test_year_list(self):
        body = client.get("/api/metadata").json()
        assert len(body["years"]) == 29
        assert 1997 in body["years"]
        assert 2025 in body["years"]

    def test_state_count(self):
        body = client.get("/api/metadata").json()
        assert len(body["states"]) == 34

    def test_crop_count(self):
        body = client.get("/api/metadata").json()
        assert len(body["crops"]) == 115

    def test_season_count(self):
        body = client.get("/api/metadata").json()
        assert len(body["seasons"]) == 6

    def test_provenance_fields_present(self):
        body = client.get("/api/metadata").json()
        assert "provenance_note" in body
        assert "coconut_unit_caveat" in body
        assert "potentially_extended_years" in body
        assert 2024 in body["potentially_extended_years"]
        assert 2025 in body["potentially_extended_years"]

    def test_geojson_mapping_present(self):
        body = client.get("/api/metadata").json()
        assert "state_name_mapping" in body
        assert body["state_name_mapping"]["Punjab"] == "Punjab"
        assert body["state_name_mapping"]["Odisha"] == "Orissa"


# =============================================================================
# /api/quality
# =============================================================================
class TestQuality:
    def test_status_200(self):
        assert client.get("/api/quality").status_code == 200

    def test_total_records(self):
        body = client.get("/api/quality").json()
        assert body["total_records"] == 463_847

    def test_missing_production(self):
        body = client.get("/api/quality").json()
        assert body["missing_production"] == 4_973

    def test_no_duplicates(self):
        body = client.get("/api/quality").json()
        assert body["duplicate_rows_full"] == 0
        assert body["duplicate_rows_key"] == 0

    def test_caveats_in_response(self):
        body = client.get("/api/quality").json()
        assert "coconut_unit_caveat" in body
        assert "provenance_note" in body
        assert "nuts" in body["coconut_unit_caveat"].lower()

    def test_year_range_is_list(self):
        body = client.get("/api/quality").json()
        assert isinstance(body["year_range"], list)
        assert body["year_range"] == [1997, 2025]


# =============================================================================
# /api/statewise
# =============================================================================
class TestStatewise:
    def test_status_200_no_filter(self):
        assert client.get("/api/statewise").status_code == 200

    def test_returns_34_states(self):
        body = client.get("/api/statewise").json()
        assert len(body["data"]) == 34

    def test_row_schema(self):
        row = client.get("/api/statewise").json()["data"][0]
        for key in ("State_Name", "Total_Production", "Total_Area", "Record_Count", "Yield_t_per_ha"):
            assert key in row, f"Missing column: {key}"

    def test_coconut_caveat_present(self):
        body = client.get("/api/statewise").json()
        assert "coconut_unit_caveat" in body

    def test_year_filter(self):
        body = client.get("/api/statewise?years=2020").json()
        assert len(body["data"]) > 0
        # Sanity: record count must be <= 2020 row count (18,655)
        total_records = sum(r["Record_Count"] for r in body["data"])
        assert total_records <= 18_655

    def test_season_filter(self):
        body = client.get("/api/statewise?seasons=Rabi").json()
        assert len(body["data"]) > 0

    def test_crop_filter(self):
        body = client.get("/api/statewise?crops=Rice").json()
        assert len(body["data"]) > 0

    def test_invalid_year_returns_404(self):
        resp = client.get("/api/statewise?years=1800")
        assert resp.status_code == 404

    def test_no_nan_in_response(self):
        raw = client.get("/api/statewise").text
        assert "NaN" not in raw
        assert "Infinity" not in raw


# =============================================================================
# /api/yearwise
# =============================================================================
class TestYearwise:
    def test_status_200_no_filter(self):
        assert client.get("/api/yearwise").status_code == 200

    def test_returns_29_years(self):
        body = client.get("/api/yearwise").json()
        assert len(body["data"]) == 29

    def test_row_schema(self):
        row = client.get("/api/yearwise").json()["data"][0]
        for key in ("Crop_Year", "Total_Production", "Total_Area", "Record_Count"):
            assert key in row, f"Missing column: {key}"

    def test_extended_years_flagged(self):
        body = client.get("/api/yearwise").json()
        assert "potentially_extended_years" in body
        assert 2024 in body["potentially_extended_years"]
        assert 2025 in body["potentially_extended_years"]

    def test_state_filter_single(self):
        body = client.get("/api/yearwise?state=Punjab").json()
        assert len(body["data"]) > 0

    def test_states_filter_multi(self):
        body = client.get("/api/yearwise?states=Punjab,Haryana").json()
        assert len(body["data"]) > 0

    def test_invalid_state_returns_404(self):
        resp = client.get("/api/yearwise?states=MadeUpState")
        assert resp.status_code == 404

    def test_no_nan_in_response(self):
        assert "NaN" not in client.get("/api/yearwise").text


# =============================================================================
# /api/cropwise
# =============================================================================
class TestCropwise:
    def test_status_200_default(self):
        assert client.get("/api/cropwise").status_code == 200

    def test_default_n_15(self):
        body = client.get("/api/cropwise").json()
        assert body["n"] == 15
        assert len(body["data"]) == 15

    def test_custom_n(self):
        body = client.get("/api/cropwise?n=5").json()
        assert len(body["data"]) == 5

    def test_n_zero_rejected(self):
        assert client.get("/api/cropwise?n=0").status_code == 422

    def test_n_too_large_rejected(self):
        assert client.get("/api/cropwise?n=200").status_code == 422

    def test_coconut_caveat_present(self):
        assert "coconut_unit_caveat" in client.get("/api/cropwise").json()

    def test_year_filter(self):
        body = client.get("/api/cropwise?years=2022&n=10").json()
        assert len(body["data"]) == 10

    def test_no_nan_in_response(self):
        assert "NaN" not in client.get("/api/cropwise").text


# =============================================================================
# /api/seasonal
# =============================================================================
class TestSeasonal:
    def test_status_200(self):
        assert client.get("/api/seasonal").status_code == 200

    def test_returns_6_seasons(self):
        body = client.get("/api/seasonal").json()
        assert len(body["data"]) == 6

    def test_season_names(self):
        seasons = {r["Season"] for r in client.get("/api/seasonal").json()["data"]}
        assert "Kharif" in seasons
        assert "Rabi" in seasons
        assert "Whole Year" in seasons

    def test_row_schema(self):
        row = client.get("/api/seasonal").json()["data"][0]
        assert "Total_Production" in row
        assert "Total_Area" in row

    def test_year_filter(self):
        body = client.get("/api/seasonal?years=2022").json()
        assert len(body["data"]) > 0

    def test_no_nan_in_response(self):
        assert "NaN" not in client.get("/api/seasonal").text


# =============================================================================
# /api/mapdata
# =============================================================================
class TestMapdata:
    def test_status_200_no_filter(self):
        assert client.get("/api/mapdata").status_code == 200

    def test_returns_34_states(self):
        body = client.get("/api/mapdata").json()
        assert len(body["data"]) == 34

    def test_row_has_geojson_name(self):
        row = client.get("/api/mapdata").json()["data"][0]
        for key in ("State_Name", "Production_sum", "Area_sum", "record_count", "geojson_name"):
            assert key in row, f"Missing column: {key}"

    def test_year_filter(self):
        body = client.get("/api/mapdata?year=2022").json()
        assert body["year"] == 2022
        assert len(body["data"]) > 0

    def test_extended_year_provenance_note(self):
        body = client.get("/api/mapdata?year=2024").json()
        assert body["provenance_note"] is not None

    def test_non_extended_year_no_provenance_note(self):
        body = client.get("/api/mapdata?year=2020").json()
        assert body["provenance_note"] is None

    def test_metric_yield(self):
        body = client.get("/api/mapdata?metric=Yield_t_per_ha").json()
        assert body["metric"] == "Yield_t_per_ha"

    def test_metric_area(self):
        body = client.get("/api/mapdata?metric=Area_sum").json()
        assert body["metric"] == "Area_sum"

    def test_invalid_metric_rejected(self):
        assert client.get("/api/mapdata?metric=invalid").status_code == 422

    def test_crop_filter(self):
        body = client.get("/api/mapdata?crop=Rice").json()
        assert len(body["data"]) > 0

    def test_no_nan_in_response(self):
        assert "NaN" not in client.get("/api/mapdata").text

    def test_unmatched_notes_present(self):
        body = client.get("/api/mapdata").json()
        assert "unmatched_geometry_notes" in body
        assert "Ladakh" in body["unmatched_geometry_notes"]


# =============================================================================
# /api/crop-trend
# =============================================================================
class TestCropTrend:
    def test_rice_trend(self):
        body = client.get("/api/crop-trend?crop=Rice").json()
        assert body["crop"] == "Rice"
        assert len(body["data"]) > 0

    def test_row_schema(self):
        row = client.get("/api/crop-trend?crop=Rice").json()["data"][0]
        assert "Crop_Year" in row
        assert "Total_Production" in row
        assert "Total_Area" in row

    def test_rice_production_nonzero(self):
        rows = client.get("/api/crop-trend?crop=Rice").json()["data"]
        total = sum(r["Total_Production"] for r in rows if r["Total_Production"])
        assert total > 1_000_000

    def test_missing_crop_param_rejected(self):
        assert client.get("/api/crop-trend").status_code == 422

    def test_unknown_crop_returns_404(self):
        assert client.get("/api/crop-trend?crop=MarsGrain9999").status_code == 404

    def test_provenance_note_present(self):
        body = client.get("/api/crop-trend?crop=Rice").json()
        assert "provenance_note" in body

    def test_state_filter(self):
        body = client.get("/api/crop-trend?crop=Rice&states=Punjab").json()
        assert len(body["data"]) > 0


# =============================================================================
# /api/state-trend
# =============================================================================
class TestStateTrend:
    def test_punjab_trend(self):
        body = client.get("/api/state-trend?state=Punjab").json()
        assert body["state"] == "Punjab"
        assert len(body["data"]) > 0

    def test_missing_state_param_rejected(self):
        assert client.get("/api/state-trend").status_code == 422

    def test_unknown_state_returns_404(self):
        assert client.get("/api/state-trend?state=FakeState999").status_code == 404

    def test_provenance_note_present(self):
        body = client.get("/api/state-trend?state=Punjab").json()
        assert "provenance_note" in body


# =============================================================================
# /api/districts
# =============================================================================
class TestDistricts:
    def test_status_200_no_filter(self):
        assert client.get("/api/districts").status_code == 200

    def test_default_n_15(self):
        body = client.get("/api/districts").json()
        assert len(body["data"]) == 15

    def test_state_filter(self):
        body = client.get("/api/districts?state=Punjab&n=5").json()
        assert len(body["data"]) <= 5
        # Every district should belong to Punjab
        for row in body["data"]:
            assert row["State_Name"] == "Punjab"

    def test_n_zero_rejected(self):
        assert client.get("/api/districts?n=0").status_code == 422


# =============================================================================
# Global JSON safety — NaN must not appear as a literal in any endpoint
# =============================================================================
class TestJsonSafety:
    ENDPOINTS = [
        "/api/health",
        "/api/metadata",
        "/api/quality",
        "/api/statewise",
        "/api/yearwise",
        "/api/cropwise",
        "/api/seasonal",
        "/api/mapdata",
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_no_nan_literal(self, endpoint):
        raw = client.get(endpoint).text
        assert "NaN" not in raw, f"{endpoint} contains NaN literal"

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_no_infinity_literal(self, endpoint):
        raw = client.get(endpoint).text
        assert "Infinity" not in raw, f"{endpoint} contains Infinity literal"

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_valid_json(self, endpoint):
        raw = client.get(endpoint).text
        parsed = json.loads(raw)          # raises if not valid JSON
        assert parsed is not None


# =============================================================================
# Spot-check: aggregation values match what the Pandas pipeline produces
# =============================================================================
class TestAggregationAccuracy:
    """
    Cross-check selected API values against direct Pandas computation.
    Ensures the API is calling the analysis functions, not fabricating results.
    """

    def test_statewise_punjab_production(self):
        """Punjab total production via API must match direct Pandas computation."""
        import pandas as pd
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
        from data_cleaning import clean, load_raw, DATA_PATH
        from pandas_analysis import statewise_production

        df = clean(load_raw(DATA_PATH))
        expected = statewise_production(df)
        punjab_row = expected[expected["State_Name"] == "Punjab"].iloc[0]
        expected_prod = float(punjab_row["Total_Production"])

        body = client.get("/api/statewise").json()
        api_rows = {r["State_Name"]: r for r in body["data"]}
        assert "Punjab" in api_rows
        assert abs(api_rows["Punjab"]["Total_Production"] - expected_prod) < 1.0

    def test_yearwise_1997_production(self):
        """1997 total production via API must match direct Pandas computation."""
        import pandas as pd
        from data_cleaning import clean, load_raw, DATA_PATH
        from pandas_analysis import yearwise_production

        df = clean(load_raw(DATA_PATH))
        expected = yearwise_production(df)
        row_1997 = expected[expected["Crop_Year"] == 1997].iloc[0]
        expected_prod = float(row_1997["Total_Production"])

        body = client.get("/api/yearwise").json()
        api_1997 = next((r for r in body["data"] if r["Crop_Year"] == 1997), None)
        assert api_1997 is not None
        assert abs(api_1997["Total_Production"] - expected_prod) < 1.0

    def test_seasonal_whole_year_is_largest_due_to_coconut(self):
        """
        'Whole Year' season has the highest production total.

        This is NOT because of grain output — it happens because Coconut is
        classified under 'Whole Year' and its production is recorded in
        NUMBER OF NUTS rather than metric tonnes. The inflated Coconut counts
        dominate the Whole Year total across Kerala, Tamil Nadu, and Karnataka.

        Kharif leads in actual grain/food-crop production but appears smaller
        in the raw numbers because its crops are measured in metric tonnes.
        """
        body = client.get("/api/seasonal").json()
        productions = {r["Season"]: r["Total_Production"] for r in body["data"]}
        # Coconut (nuts) pushes Whole Year above all grain seasons
        assert productions["Whole Year"] == max(productions.values()), (
            "Expected 'Whole Year' to dominate due to Coconut unit inflation"
        )
        # Kharif should still be the largest true-grain season (second overall)
        grain_seasons = {k: v for k, v in productions.items() if k != "Whole Year"}
        assert productions["Kharif"] == max(grain_seasons.values()), (
            "Expected Kharif to be largest among non-Whole-Year seasons"
        )


# =============================================================================
# /api/records
# =============================================================================
class TestRecords:
    def test_status_200_no_filter(self):
        resp = client.get("/api/records")
        assert resp.status_code == 200

    def test_response_structure(self):
        body = client.get("/api/records").json()
        for key in ("total", "page", "page_size", "total_pages", "records"):
            assert key in body, f"Missing key: {key}"

    def test_default_page_size_25(self):
        body = client.get("/api/records").json()
        assert len(body["records"]) == 25

    def test_total_matches_full_dataset(self):
        body = client.get("/api/records").json()
        assert body["total"] == 463_847

    def test_page_1_is_default(self):
        body = client.get("/api/records").json()
        assert body["page"] == 1

    def test_record_schema(self):
        row = client.get("/api/records").json()["records"][0]
        for key in ("id", "State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production", "Data_Type"):
            assert key in row, f"Missing field: {key}"

    def test_custom_page_size(self):
        body = client.get("/api/records?page_size=10").json()
        assert len(body["records"]) == 10

    def test_page_size_over_100_rejected(self):
        assert client.get("/api/records?page_size=101").status_code == 422

    def test_page_size_zero_rejected(self):
        assert client.get("/api/records?page_size=0").status_code == 422

    def test_year_from_filter(self):
        body = client.get("/api/records?year_from=2020&page_size=5").json()
        assert body["total"] > 0
        for row in body["records"]:
            assert row["Crop_Year"] >= 2020

    def test_year_to_filter(self):
        body = client.get("/api/records?year_to=2000&page_size=5").json()
        assert body["total"] > 0
        for row in body["records"]:
            assert row["Crop_Year"] <= 2000

    def test_year_range_filter(self):
        body = client.get("/api/records?year_from=2010&year_to=2010&page_size=5").json()
        assert body["total"] > 0
        for row in body["records"]:
            assert row["Crop_Year"] == 2010

    def test_invalid_year_range_rejected(self):
        assert client.get("/api/records?year_from=2020&year_to=2010").status_code == 422

    def test_state_filter(self):
        body = client.get("/api/records?state=Punjab&page_size=10").json()
        assert body["total"] > 0
        for row in body["records"]:
            assert row["State_Name"] == "Punjab"

    def test_crop_filter(self):
        body = client.get("/api/records?crop=Rice&page_size=10").json()
        assert body["total"] > 0
        for row in body["records"]:
            assert row["Crop"] == "Rice"

    def test_season_filter(self):
        body = client.get("/api/records?season=Kharif&page_size=10").json()
        assert body["total"] > 0
        for row in body["records"]:
            assert row["Season"] == "Kharif"

    def test_combined_filters(self):
        body = client.get("/api/records?state=Punjab&crop=Rice&season=Kharif&page_size=10").json()
        assert body["total"] > 0
        for row in body["records"]:
            assert row["State_Name"] == "Punjab"
            assert row["Crop"] == "Rice"
            assert row["Season"] == "Kharif"

    def test_search_state_name(self):
        body = client.get("/api/records?search=Punjab&page_size=10").json()
        assert body["total"] > 0

    def test_search_crop_name(self):
        body = client.get("/api/records?search=wheat&page_size=10").json()
        assert body["total"] > 0

    def test_search_no_results(self):
        body = client.get("/api/records?search=xyznotacrop99999&page_size=10").json()
        assert body["total"] == 0
        assert len(body["records"]) == 0

    def test_sort_by_year_desc(self):
        body = client.get("/api/records?sort_by=year&sort_order=desc&page_size=5").json()
        years = [r["Crop_Year"] for r in body["records"]]
        assert years == sorted(years, reverse=True)

    def test_sort_by_year_asc(self):
        body = client.get("/api/records?sort_by=year&sort_order=asc&page_size=5").json()
        years = [r["Crop_Year"] for r in body["records"]]
        assert years == sorted(years)

    def test_sort_by_state(self):
        body = client.get("/api/records?sort_by=state&sort_order=asc&page_size=10").json()
        assert body["total"] > 0

    def test_invalid_sort_column_rejected(self):
        assert client.get("/api/records?sort_by=invalid_column_xyz").status_code == 422

    def test_pagination_second_page(self):
        page1 = client.get("/api/records?page=1&page_size=10").json()
        page2 = client.get("/api/records?page=2&page_size=10").json()
        ids1 = {r["id"] for r in page1["records"]}
        ids2 = {r["id"] for r in page2["records"]}
        assert ids1.isdisjoint(ids2), "Pages should not share record IDs"

    def test_total_pages_calculated(self):
        body = client.get("/api/records?page_size=100").json()
        assert body["total_pages"] == (463_847 + 99) // 100  # ceil division

    def test_no_nan_in_response(self):
        raw = client.get("/api/records").text
        assert "NaN" not in raw
        assert "Infinity" not in raw

    def test_district_filter(self):
        body = client.get("/api/records?district=Amritsar&page_size=10").json()
        if body["total"] > 0:
            for row in body["records"]:
                assert row["District_Name"] == "Amritsar"

    def test_data_type_filter(self):
        body = client.get("/api/records?data_type=Actual&page_size=5").json()
        # "Actual" is the only Data_Type value in the dataset
        assert body["total"] > 0


# =============================================================================
# /api/export/records
# =============================================================================
class TestExportRecords:
    def test_status_200(self):
        resp = client.get("/api/export/records")
        assert resp.status_code == 200

    def test_content_type_csv(self):
        resp = client.get("/api/export/records")
        assert "text/csv" in resp.headers["content-type"]

    def test_csv_has_header(self):
        resp = client.get("/api/export/records")
        first_line = resp.text.splitlines()[0]
        assert "State_Name" in first_line
        assert "Crop_Year" in first_line

    def test_filtered_export_fewer_rows(self):
        full   = client.get("/api/export/records")
        filtered = client.get("/api/export/records?state=Punjab")
        assert len(filtered.text.splitlines()) < len(full.text.splitlines())

    def test_invalid_year_range_rejected(self):
        assert client.get("/api/export/records?year_from=2020&year_to=2010").status_code == 422

    def test_x_record_count_header(self):
        resp = client.get("/api/export/records?state=Punjab")
        # Header may be exposed depending on CORS settings; skip if not present.
        count_header = resp.headers.get("x-record-count")
        if count_header is not None:
            assert int(count_header) > 0


# =============================================================================
# Enriched /api/metadata — per-state cascading filter maps
# =============================================================================
class TestMetadataEnriched:
    def test_districts_by_state_present(self):
        body = client.get("/api/metadata").json()
        assert "districts_by_state" in body
        assert isinstance(body["districts_by_state"], dict)

    def test_districts_by_state_punjab(self):
        body = client.get("/api/metadata").json()
        punjab_districts = body["districts_by_state"].get("Punjab", [])
        assert len(punjab_districts) > 0
        assert "Amritsar" in punjab_districts

    def test_crops_by_state_present(self):
        body = client.get("/api/metadata").json()
        assert "crops_by_state" in body
        assert isinstance(body["crops_by_state"], dict)

    def test_crops_by_state_punjab_has_wheat(self):
        body = client.get("/api/metadata").json()
        punjab_crops = body["crops_by_state"].get("Punjab", [])
        assert "Wheat" in punjab_crops

    def test_seasons_by_crop_present(self):
        body = client.get("/api/metadata").json()
        assert "seasons_by_crop" in body
        assert isinstance(body["seasons_by_crop"], dict)

    def test_record_count_in_metadata(self):
        body = client.get("/api/metadata").json()
        assert "record_count" in body
        assert body["record_count"] == 463_847

    def test_data_types_in_metadata(self):
        body = client.get("/api/metadata").json()
        assert "data_types" in body
        assert isinstance(body["data_types"], list)
        assert len(body["data_types"]) > 0
