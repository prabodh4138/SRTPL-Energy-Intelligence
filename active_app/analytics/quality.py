def quality_summary(total_records, valid_records, invalid_records=0, duplicates=0, exceptions=0):
    return {
      "records_received": total_records,
      "valid_records": valid_records,
      "invalid_records": invalid_records,
      "duplicates": duplicates,
      "exceptions": exceptions,
      "completeness_percent": valid_records/total_records*100 if total_records else None,
      "duplicate_rate_percent": duplicates/total_records*100 if total_records else None,
      "exception_rate_percent": exceptions/total_records*100 if total_records else None
    }
