import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieListResponseSchema, MovieDetailResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def movie_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Items per page",
    ),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    movies_count_query = select(func.count(MovieModel.id))
    movies_count_result = await db.execute(movies_count_query)
    movies_count = movies_count_result.scalar_one()

    movies_query = (
        select(MovieModel).offset((page - 1) * per_page).limit(per_page)
    )
    movies_result = await db.execute(movies_query)
    movies = movies_result.scalars().all()

    if len(movies) == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    if prev_page := page - 1 > 0:
        prev_page = f"/theater/movies/?page={prev_page}&per_page={per_page}"
    else:
        prev_page = None

    total_pages = math.ceil(movies_count / per_page)

    if next_page := page + 1 < total_pages:
        next_page = f"/theater/movies/?page={next_page}&per_page={per_page}"
    else:
        next_page = None

    return MovieListResponseSchema(
        movies=movies,
        total_items=movies_count,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def movie_detail(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailResponseSchema:
    movie_query = select(MovieModel).filter(MovieModel.id == movie_id)
    movie_result = await db.execute(movie_query)
    movie = movie_result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie
