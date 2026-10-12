// Shows a loading / error message; renders nothing when data is ready.
export default function Status({ loading, error, hasData }) {
  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Could not reach the API: {error}. Is the backend running on port 8000?
      </div>
    );
  }
  if (loading && !hasData) {
    return <p className="py-8 text-center text-sm text-slate-500">Loading...</p>;
  }
  return null;
}
