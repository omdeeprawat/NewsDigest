from app.runner import run_scrapers


def main(hours=24):
  results = run_scrapers(hours=hours)
  print(f"youtube videos : {len(results['youtube'])}")
  print(f"openai articles : {len(results['openai'])}")
  print(f"anthropic articles : {len(results['anthropic'])}")

  return results

if __name__ == "__main__":
    print("__main__ BLOCK STARTED")
    main(hours = 150)